from datetime import datetime


def add_months(date_obj, months):
    month = date_obj.month - 1 + months
    year = date_obj.year + month // 12
    month = month % 12 + 1
    day = min(date_obj.day, [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    ][month - 1])
    return date_obj.replace(year=year, month=month, day=day)

def calculate_expiry(data_classification, input_date):
    date_obj = datetime.strptime(input_date, "%Y/%m/%d")

    if data_classification == "Business Use (1 year)":
        expiry_date = date_obj.replace(year=date_obj.year + 1)
    elif data_classification == "Highly Restricted (180 days)":
        expiry_date = add_months(date_obj, 6)
    elif data_classification == "Secret (90 days)":
        expiry_date = add_months(date_obj, 3)
    else:
        raise ValueError("Invalid Data Classification")

    return expiry_date.strftime("%Y/%m/%d")

if __name__ == "__main__":
    print("Choose Data Classification:")
    print("1 - Business Use (1 year)")
    print("2 - Highly Restricted (180 days)")
    print("3 - Secret (90 days)")

    choice = input("Enter choice (1/2/3): ").strip()
    date_input = input("Enter start date (YYYY/MM/DD): ").strip()

    classification_map = {
        "1": "Business Use (1 year)",
        "2": "Highly Restricted (180 days)",
        "3": "Secret (90 days)"
    }

    data_classification = classification_map.get(choice)

    if not data_classification:
        print("Invalid selection")
    else:
        result = calculate_expiry(data_classification, date_input)
        print(f"Output Date: {result}")