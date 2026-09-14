import pandas as pd
from django.core.management.base import BaseCommand
from DataAnalysis.models import FoodItems


class Command(BaseCommand):
    help = "Import food items from an Excel file"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str, help="Path to the Excel file")

    def handle(self, *args, **options):
        file_path = options["excel_file"]
        df = pd.read_excel(file_path)

        created_count = 0
        updated_count = 0

        for _, row in df.iterrows():
            food_name = str(row["food_name"]).strip()
            sepdar_code = str(row.get("sepdar_code", "")).strip() or None
            foodsoft_code = str(row.get("foodsoft_code", "")).strip() or None

            obj, created = FoodItems.objects.update_or_create(
                food_name=food_name,
                defaults={
                    "sepdar_code": sepdar_code,
                    "foodsoft_code": foodsoft_code,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_count}, Updated: {updated_count}"
            )
        )