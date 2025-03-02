import sqlite3
import os

def migrate_database():
    """
    Выполняет миграцию базы данных, добавляя поле is_premium в таблицу announcements
    """
    # Путь к файлу базы данных
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    # Проверяем существование файла
    if not os.path.exists(db_path):
        print(f"База данных не найдена по пути: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже колонка is_premium в таблице announcements
        cursor.execute("PRAGMA table_info(announcements)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'is_premium' not in column_names:
            # Добавляем колонку is_premium
            cursor.execute("ALTER TABLE announcements ADD COLUMN is_premium BOOLEAN DEFAULT 0")
            
            # Обновляем значения is_premium на основе премиум-статуса пользователей
            cursor.execute("""
                UPDATE announcements 
                SET is_premium = (
                    SELECT is_premium FROM users 
                    WHERE users.id = announcements.user_id
                )
            """)
            
            conn.commit()
            print("Миграция успешно выполнена. Добавлена колонка is_premium в таблицу announcements.")
        else:
            print("Колонка is_premium уже существует в таблице announcements.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        return False

if __name__ == "__main__":
    migrate_database() 