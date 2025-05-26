import asyncio
import os
import uuid
import matplotlib.pyplot as plt

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

class KreditState(StatesGroup):
    summani_kiritish = State()
    muddatni_kiritish = State()

def annuitet_kredit_jadvali(summasi, oy_soni, yillik_foiz=56):
    oylik_foiz = yillik_foiz / 12 / 100
    annuitet_tolov = summasi * (oylik_foiz * (1 + oylik_foiz) ** oy_soni) / ((1 + oylik_foiz) ** oy_soni - 1)
    jadval = []
    qoldiq = summasi
    for oy in range(1, oy_soni + 1):
        foiz_tolovi = qoldiq * oylik_foiz
        asosiy_qaytarish = annuitet_tolov - foiz_tolovi
        qoldiq -= asosiy_qaytarish
        jadval.append([
            f"{oy}-oy",
            round(foiz_tolovi),
            round(asosiy_qaytarish),
            round(annuitet_tolov),
            round(max(qoldiq, 0))
        ])
    return jadval

def differensial_kredit_jadvali(summasi, oy_soni, yillik_foiz=56):
    oylik_foiz = yillik_foiz / 12 / 100
    asosiy_qaytarish = summasi / oy_soni
    jadval = []
    qoldiq = summasi
    for oy in range(1, oy_soni + 1):
        foiz_tolovi = qoldiq * oylik_foiz
        umumiy_tolov = asosiy_qaytarish + foiz_tolovi
        qoldiq -= asosiy_qaytarish
        jadval.append([
            f"{oy}-oy",
            round(foiz_tolovi),
            round(asosiy_qaytarish),
            round(umumiy_tolov),
            round(max(qoldiq, 0))
        ])
    return jadval

def format_summa(val):
    return f"{int(round(val)):,}".replace(",", " ")

def draw_table_image(jadval, title, filename, muddat):
    fig, ax = plt.subplots(figsize=(11.7, 8.3))  # A4
    ax.axis('off')

    jami_foiz = sum(row[1] for row in jadval)
    jami_tolov = sum(row[3] for row in jadval)

    table_data = [["Sana", "Foizlar", "Asosiy qarz", "Oylik to‘lov", "Qoldiq summa"]]
    for row in jadval:
        table_data.append([
            row[0],
            format_summa(row[1]),
            format_summa(row[2]),
            format_summa(row[3]),
            format_summa(row[4])
        ])
    table_data.append([
        "Jami",
        format_summa(jami_foiz),
        "-",
        format_summa(jami_tolov),
        "-"
    ])

    rows = len(table_data)
    table = ax.table(
        cellText=table_data,
        loc='center',
        cellLoc='center',
        colLabels=None,
        bbox=[0, 0, 1, 1]
    )

    # Dinamik font size va padding
    if muddat <= 12:
        font_size = 12
        cell_padding = 0.05
    elif muddat <= 24:
        font_size = 10
        cell_padding = 0.04
    elif muddat <= 36:
        font_size = 8
        cell_padding = 0.035
    elif muddat <= 48:
        font_size = 7
        cell_padding = 0.03
    elif muddat <= 60:
        font_size = 6
        cell_padding = 0.025
    elif muddat <= 72:
        font_size = 5.5
        cell_padding = 0.02
    else:
        font_size = 5
        cell_padding = 0.015

    table.auto_set_font_size(False)
    table.set_fontsize(font_size)

    # Katak ranglari va chiziqlar
    for row in range(1, rows - 1):
        color = '#f9f9f9' if row % 2 == 0 else '#ffffff'
        for col in range(5):
            table[(row, col)].set_facecolor(color)

    header_color = '#cceeff'
    tolov_color = '#e0e0e0'
    for col in range(5):
        table[(0, col)].set_facecolor(header_color)
        table[(0, col)].set_text_props(weight='bold')
        table[(rows - 1, col)].set_text_props(weight='bold')

    for row in range(1, rows):
        table[(row, 3)].set_facecolor(tolov_color)
        table[(row, 3)].set_text_props(weight='bold')

    for row in range(rows):
        for col in range(5):
            cell = table[(row, col)]
            cell.set_linewidth(0.5)
            cell.set_edgecolor("black")
            cell.set_text_props(fontsize=font_size)
            cell.PAD = cell_padding

    fig.suptitle(title, fontsize=14, weight='bold')

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    plt.savefig(file_path, format='png', dpi=300)
    plt.close()

    return file_path, round(jami_foiz), round(jami_tolov)

# Bot komandalar
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Kredit hisoblash uchun /kredit buyrug‘ini bosing.")

@dp.message(Command("kredit"))
async def kredit_start(message: Message, state: FSMContext):
    await state.set_state(KreditState.summani_kiritish)
    await message.answer("Kredit summasini kiriting (so‘m):")

@dp.message(KreditState.summani_kiritish)
async def get_sum(message: Message, state: FSMContext):
    try:
        summa = float(message.text.replace(" ", ""))
        if not 3_000_000 <= summa <= 300_000_000:
            await message.answer("❌ Kredit summasi 3 000 000 dan 300 000 000 so‘mgacha bo‘lishi kerak.")
            return
        await state.update_data(summasi=summa)
        await state.set_state(KreditState.muddatni_kiritish)
        await message.answer("✅ Endi kredit muddatini oyda kiriting (masalan: 12):\n<i>3 oydan 48 oygacha</i>")
    except ValueError:
        await message.answer("❗️ Iltimos, faqat raqam kiriting! Masalan: <code>12000000</code>")

@dp.message(KreditState.muddatni_kiritish)
async def get_muddat(message: Message, state: FSMContext):
    try:
        muddat = int(message.text.strip())
        if not 3 <= muddat <= 48:
            await message.answer("❌ Kredit muddati 3 oydan 48 oygacha bo‘lishi kerak.")
            return

        data = await state.get_data()
        summa = data['summasi']
        # Noyob fayl nomlari
        annuitet_filename = f"annuitet_{uuid.uuid4().hex}.png"
        differensial_filename = f"differensial_{uuid.uuid4().hex}.png"

        annuitet = annuitet_kredit_jadvali(summa, muddat)
        differensial = differensial_kredit_jadvali(summa, muddat)

        annuitet_path, annuitet_jami_foiz, annuitet_jami_tolov = draw_table_image(
            annuitet, "Annuitet Kredit Jadvali", annuitet_filename, muddat
        )
        differensial_path, differensial_jami_foiz, differensial_jami_tolov = draw_table_image(
            differensial, "Differensial Kredit Jadvali", differensial_filename, muddat
        )

        await message.answer_photo(
            FSInputFile(annuitet_path),
            caption=f"<b>Annuitet jadvali</b>\nJami foiz: <code>{format_summa(annuitet_jami_foiz)}</code> so‘m\nJami to‘lov: <code>{format_summa(annuitet_jami_tolov)}</code> so‘m"
        )
        os.remove(annuitet_path)

        await message.answer_photo(
            FSInputFile(differensial_path),
            caption=f"<b>Differensial jadvali</b>\nJami foiz: <code>{format_summa(differensial_jami_foiz)}</code> so‘m\nJami to‘lov: <code>{format_summa(differensial_jami_tolov)}</code> so‘m"
        )
        os.remove(differensial_path)

        await state.clear()

    except ValueError:
        await message.answer("Iltimos, to‘g‘ri raqam kiriting!")

# Asosiy ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
