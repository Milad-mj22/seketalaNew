import pandas as pd
from django.core.management.base import BaseCommand
from DataAnalysis.models import FoodItems


class Command(BaseCommand):
    help = "Import food_name + foodsoft_code from Excel"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str)

    def handle(self, *args, **options):
        df = pd.read_excel(options["excel_file"])

        # اگر هدرها فرق داشت اینجا رنیم کن
        df = df.rename(columns={
            "نام غذا": "food_name",
            "کد فود سافت": "foodsoft_code",
        })

        created = 0
        updated = 0

        for _, row in df.iterrows():
            food_name = str(row["food_name"]).strip()
            foodsoft_code = str(row["foodsoft_code"]).strip()

            if not food_name or food_name.lower() == "nan":
                continue

            obj, is_created = FoodItems.objects.update_or_create(
                food_name=food_name,
                defaults={"foodsoft_code": foodsoft_code},
            )
            created += is_created
            updated += not is_created

        self.stdout.write(self.style.SUCCESS(
            f"Foodsoft import done. Created: {created}, Updated: {updated}"
        ))