# batch_processor.py
from order_mapping import transform_orders_batch


def main():
    message = transform_orders_batch()
    # Minimal debug print so you can check the import works in the Kestra logs
    print(f"[DEBUG] transform_orders_batch → {message}")


if __name__ == "__main__":
    main()
