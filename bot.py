import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "替换你的TOKEN"
ADMIN_ID = 123456789

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB = "database.db"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        wallet TEXT,
        remark TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


class WalletState(StatesGroup):
    waiting_wallet = State()
    waiting_remark = State()


class AdState(StatesGroup):
    waiting_ad = State()


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ 添加监控",
                    callback_data="add_wallet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 我的钱包",
                    callback_data="my_wallets"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 开通VIP",
                    callback_data="vip"
                )
            ]
        ]
    )


def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ 添加广告",
                    callback_data="add_ad"
                )
            ]
        ]
    )


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "💰 USDT监控助手",
        reply_markup=main_menu()
    )


@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙️ 超级管理后台",
        reply_markup=admin_menu()
    )


@dp.callback_query(F.data == "add_wallet")
async def add_wallet_click(call: CallbackQuery, state: FSMContext):
    await state.set_state(WalletState.waiting_wallet)

    await call.message.answer("请输入TRC20钱包地址")


@dp.message(WalletState.waiting_wallet)
async def save_wallet(message: Message, state: FSMContext):
    wallet = message.text.strip()

    await state.update_data(wallet=wallet)

    await state.set_state(WalletState.waiting_remark)

    await message.answer("请输入钱包备注")


@dp.message(WalletState.waiting_remark)
async def save_remark(message: Message, state: FSMContext):
    data = await state.get_data()

    wallet = data["wallet"]
    remark = message.text.strip()

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT INTO wallets(chat_id,wallet,remark) VALUES(?,?,?)",
        (
            message.chat.id,
            wallet,
            remark
        )
    )

    conn.commit()
    conn.close()

    await state.clear()

    await message.answer(
        f"✅ 添加成功\\n\\n👛 地址：{wallet}\\n📝 备注：{remark}"
    )


@dp.callback_query(F.data == "my_wallets")
async def my_wallets(call: CallbackQuery):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "SELECT wallet,remark FROM wallets WHERE chat_id=?",
        (call.message.chat.id,)
    )

    rows = c.fetchall()

    conn.close()

    if not rows:
        await call.message.answer("暂无监控钱包")
        return

    text = "📋 监控钱包列表\\n\\n"

    for w, r in rows:
        text += f"📝 {r}\\n👛 {w}\\n\\n"

    await call.message.answer(text)


@dp.callback_query(F.data == "add_ad")
async def add_ad(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return

    await state.set_state(AdState.waiting_ad)

    await call.message.answer(
        "请输入广告内容\\n\\n格式：\\n广告标题\\n广告链接"
    )


@dp.message(AdState.waiting_ad)
async def save_ad(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lines = message.text.split("\\n")

    if len(lines) < 2:
        await message.answer("格式错误")
        return

    title = lines[0]
    url = lines[1]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT INTO ads(title,url) VALUES(?,?)",
        (title, url)
    )

    conn.commit()
    conn.close()

    await state.clear()

    await message.answer("✅ 广告添加成功")


@dp.callback_query(F.data == "vip")
async def vip(call: CallbackQuery):
    await call.message.answer(
        "💎 VIP月卡\\n\\n请支付：30点38 USDT(TRC20)"
    )


async def fake_monitor():
    while True:
        await asyncio.sleep(300)

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute(
            "SELECT chat_id,wallet,remark FROM wallets"
        )

        wallets = c.fetchall()

        c.execute(
            "SELECT title,url FROM ads"
        )

        ads = c.fetchall()

        conn.close()

        for chat_id, wallet, remark in wallets:
            amount = 58200.38

            value = (
                "{:.2f}"
                .format(amount)
                .replace(".", "点")
            )

            if amount >= 100000:
                title = "🐋 鲸鱼资金预警"

            elif amount >= 10000:
                title = "🚨 大额资金异动"

            elif amount % 1 != 0:
                title = "⚠️ 注意核对金额"

            else:
                title = "💰 USDT到账提醒"

            text = (
                f"{title}\\n\\n"
                f"👤 钱包备注：{remark}\\n\\n"
                f"💵 金额：{value} USDT\\n"
                f"📈 类型：收入\\n\\n"
                f"👛 地址：\\n{wallet}"
            )

            buttons = []

            for ad_title, ad_url in ads:
                buttons.append([
                    InlineKeyboardButton(
                        text=ad_title,
                        url=ad_url
                    )
                ])

            markup = InlineKeyboardMarkup(
                inline_keyboard=buttons
            ) if buttons else None

            try:
                await bot.send_message(
                    chat_id,
                    text,
                    reply_markup=markup
                )
            except:
                pass


async def main():
    asyncio.create_task(fake_monitor())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
