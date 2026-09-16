import pandas as pd
from django.core.management.base import BaseCommand
from DataAnalysis.models import FoodItems
from DataAnalysis.utils import normalize_fa, top_matches

import sys
import io
import re

# تنظیم encoding خروجی برای پشتیبانی از فارسی در ویندوز
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

import arabic_reshaper
from bidi.algorithm import get_display

_FA_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+')


def _reshape_fa(match):
    return get_display(arabic_reshaper.reshape(match.group(0)))


def fa(text):
    """فقط بخش‌های فارسی متن رو reshape می‌کنه؛ اعداد و علائم دست‌نخورده می‌مونن"""
    if not text:
        return text
    return _FA_PATTERN.sub(_reshape_fa, str(text))


class Command(BaseCommand):
    help = "Interactive sepdar_code import from Excel, driven by DB items"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str)
        parser.add_argument("--limit", type=int, default=5)
        parser.add_argument(
            "--only-empty",
            action="store_true",
            help="فقط آیتم‌هایی که sepdar_code خالی دارند",
        )

    def handle(self, *args, **options):
        df = pd.read_excel(options["excel_file"])
        limit = options["limit"]
        only_empty = options["only_empty"]

        df = df.rename(columns={
            "نام غذا": "food_name",
            "کد سپیدار": "sepdar_code",
        })

        # ---------- ساخت ایندکس از اکسل ----------
        excel_name_map = {}   # norm → (raw_name, sepdar_code)
        excel_choices = []
        for _, row in df.iterrows():
            raw_name = str(row["food_name"]).strip()
            sepdar_code = str(row["sepdar_code"]).strip()

            if not raw_name or raw_name.lower() == "nan":
                continue
            if not sepdar_code or sepdar_code.lower() == "nan":
                continue

            norm = normalize_fa(raw_name)
            if norm not in excel_name_map:
                excel_name_map[norm] = (raw_name, sepdar_code)
                excel_choices.append(norm)

        self.stdout.write(self.style.HTTP_INFO(
            fa(f"تعداد ردیف‌های معتبر اکسل: {len(excel_name_map)}")
        ))

        # ---------- آیتم‌های دیتابیس ----------
        db_items = list(FoodItems.objects.all())
        if only_empty:
            db_items = [i for i in db_items if not i.sepdar_code]

        self.stdout.write(self.style.HTTP_INFO(
            fa(f"تعداد آیتم‌های دیتابیس برای بررسی: {len(db_items)}")
        ))
        self.stdout.write("")

        stats = {"exact": 0, "chosen": 0, "skipped": 0, "saved": 0, "conflict": 0}

        # نگه‌داشتن کدهایی که در همین اجرا تخصیص داده شده‌اند
        # (چون قبل از save دیتابیس آپدیت نمی‌شه)
        used_codes = {}  # sepdar_code → obj.food_name

        for idx, obj in enumerate(db_items, 1):
            norm = normalize_fa(obj.food_name)

            # ---------- ۱) مچ دقیق در اکسل ----------
            if norm in excel_name_map:
                raw_name, sepdar_code = excel_name_map[norm]
                obj.sepdar_code = sepdar_code
                obj.save(update_fields=["sepdar_code"])
                self.stdout.write(self.style.SUCCESS(
                    fa(f"[{idx}] ✓ exact: {obj.food_name} → {sepdar_code}")
                ))
                stats["exact"] += 1
                stats["saved"] += 1
                continue
                        # ---------- ۲) پیشنهادهای فازی از اکسل ----------
            candidates = top_matches(norm, excel_choices, limit=limit)

            if not candidates:
                self.stdout.write(self.style.WARNING(
                    fa(f"[{idx}] – هیچ شباهتی در اکسل نبود: {obj.food_name}")
                ))
                stats["skipped"] += 1
                continue

            self.stdout.write("")
            self.stdout.write(self.style.HTTP_INFO(
                fa(f"── [{idx}] «{obj.food_name}»")
            ))
            for i, (matched_norm, score) in enumerate(candidates, 1):
                raw_name, code = excel_name_map[matched_norm]
                self.stdout.write(
                    fa(f"  [{i}] {raw_name}   (شباهت: {score:.1f} | کد: {code})")
                )
            self.stdout.write(fa("  [s] رد کردن این مورد (skip)"))
            self.stdout.write(fa("  [q] خروج از برنامه"))

            # ---------- ۳) انتخاب کاربر ----------
            choice = self._ask_choice(len(candidates))

            if choice == "q":
                self.stdout.write(self.style.WARNING(fa("خروج از برنامه.")))
                break
            if choice == "s":
                stats["skipped"] += 1
                self.stdout.write(self.style.WARNING(
                    fa(f"[{idx}] skip: {obj.food_name}")
                ))
                continue

            selected_norm = candidates[choice - 1][0]
            raw_name, sepdar_code = excel_name_map[selected_norm]
            obj.sepdar_code = sepdar_code
            obj.save(update_fields=["sepdar_code"])
            self.stdout.write(self.style.SUCCESS(
                fa(f"[{idx}] ✓ ذخیره شد: {obj.food_name} → {sepdar_code}")
            ))
            stats["chosen"] += 1
            stats["saved"] += 1

        # ---------- خلاصه ----------
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            fa(f"تمام شد. exact={stats['exact']}, "
               f"انتخاب کاربر={stats['chosen']}, "
               f"رد شده={stats['skipped']}, "
               f"تداخل کد={stats['conflict']}, "
               f"ذخیره کل={stats['saved']}")
        ))

    def _code_in_use(self, obj, sepdar_code: str, used_codes: dict) -> bool:
        """
        بررسی می‌کنه که کد سپیدار قبلاً به FoodItem دیگه‌ای داده نشده باشه.
        هم دیتابیس و هم کدهای تخصیص‌یافته در همین اجرا رو چک می‌کنه.
        اگر تکراری بود، پیام هشدار چاپ می‌کنه و True برمی‌گردونه.
        """
        # چک تکراری در دیتابیس
        existing = FoodItems.objects.filter(sepdar_code=sepdar_code).exclude(pk=obj.pk).first()
        if existing:
            self.stdout.write(self.style.ERROR(
                fa(f"  ⚠ کد {sepdar_code} قبلاً به «{existing.food_name}» داده شده → skip «{obj.food_name}»")
            ))
            return True

        # چک تکراری در همین اجرا
        if sepdar_code in used_codes:
            other = used_codes[sepdar_code]
            self.stdout.write(self.style.ERROR(
                fa(f"  ⚠ کد {sepdar_code} در همین اجرا به «{other}» داده شد → skip «{obj.food_name}»")
            ))
            return True

        return False

    def _ask_choice(self, n: int) -> str | int:
        """از کاربر انتخاب میگیرد و شماره، 's' یا 'q' برمیگرداند"""
        while True:
            try:
                raw = input(fa("انتخاب شما: ")).strip().lower()
            except (EOFError, KeyboardInterrupt):
                return "q"

            if raw in ("s", "q"):
                return raw
            if raw.isdigit():
                num = int(raw)
                if 1 <= num <= n:
                    return num
            self.stdout.write(self.style.ERROR(fa("ورودی نامعتبر. دوباره.")))