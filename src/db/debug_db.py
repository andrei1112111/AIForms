# debug_db.py

def debug_string():
    # Проверим все части строки подключения
    parts = {
        "username": "forms_user",
        "password": "forms_pass", 
        "host": "localhost",
        "port": 5432,
        "database": "metrics_db"
    }
    
    print("=== DEBUG CONNECTION STRING ===")
    for key, value in parts.items():
        print(f"{key}: {repr(value)}")
        print(f"  type: {type(value)}")
        print(f"  as bytes: {str(value).encode('utf-8')}")
        print(f"  has non-ASCII: {any(ord(c) > 127 for c in str(value))}")
        print("---")
    
    # Соберем полную строку
    full_string = f"postgresql+psycopg2://{parts['username']}:{parts['password']}@{parts['host']}:{parts['port']}/{parts['database']}"
    print(f"FULL CONNECTION STRING: {repr(full_string)}")
    print(f"Full string as bytes: {full_string.encode('utf-8')}")
    
    return full_string

if __name__ == "__main__":
    debug_string()
    print(repr(r"postgresql+psycopg2://postgres:43720@localhost:5432/metrics_db"))
