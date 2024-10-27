import aiosqlite

class Database:
    def __init__(self, db_name='zelenka_bot.db'):
        self.db_name = db_name

    async def init(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    forum_id TEXT,
                    status TEXT,
                    parameters TEXT,
                    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await db.execute('''
                CREATE TABLE IF NOT EXISTS approved_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    comment TEXT
                )
            ''')
            await db.commit()

    async def add_application(self, user_id, forum_id, parameters):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO applications 
                (user_id, forum_id, status, parameters) 
                VALUES (?, ?, 'pending', ?)
            ''', (user_id, forum_id, parameters))
            await db.commit()

    async def check_payment_exists(self, forum_id):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                'SELECT * FROM applications WHERE forum_id = ? AND status = "approved"',
                (forum_id,)
            )
            result = await cursor.fetchone()
            return bool(result)

    async def get_user_id_by_forum_id(self, forum_id):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                'SELECT user_id FROM applications WHERE forum_id = ? ORDER BY id DESC LIMIT 1',
                (forum_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else None

    async def update_application_status(self, forum_id, status):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE applications SET status = ? WHERE forum_id = ? AND status = "pending"',
                (status, forum_id)
            )
            await db.commit()

    async def get_pending_applications(self):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM applications WHERE status = ?',
                ('pending',)
            )
            return await cursor.fetchall()