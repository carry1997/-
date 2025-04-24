import sqlite3
import os
from datetime import datetime
import re


db_file = 'bookstore.db'

# 建立與初始化資料庫
def init_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS member (
            mid TEXT PRIMARY KEY,
            mname TEXT NOT NULL,
            mphone TEXT NOT NULL,
            memail TEXT
        );

        CREATE TABLE IF NOT EXISTS book (
            bid TEXT PRIMARY KEY,
            btitle TEXT NOT NULL,
            bprice INTEGER NOT NULL,
            bstock INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sale (
            sid INTEGER PRIMARY KEY AUTOINCREMENT,
            sdate TEXT NOT NULL,
            mid TEXT NOT NULL,
            bid TEXT NOT NULL,
            sqty INTEGER NOT NULL,
            sdiscount INTEGER NOT NULL,
            stotal INTEGER NOT NULL
        );

        INSERT OR IGNORE INTO member VALUES ('M001', 'Alice', '0912-345678', 'alice@example.com');
        INSERT OR IGNORE INTO member VALUES ('M002', 'Bob', '0923-456789', 'bob@example.com');
        INSERT OR IGNORE INTO member VALUES ('M003', 'Cathy', '0934-567890', 'cathy@example.com');

        INSERT OR IGNORE INTO book VALUES ('B001', 'Python Programming', 600, 50);
        INSERT OR IGNORE INTO book VALUES ('B002', 'Data Science Basics', 800, 30);
        INSERT OR IGNORE INTO book VALUES ('B003', 'Machine Learning Guide', 1200, 20);

        INSERT OR IGNORE INTO sale (sid, sdate, mid, bid, sqty, sdiscount, stotal) VALUES
            (1, '2024-01-15', 'M001', 'B001', 2, 100, 1100),
            (2, '2024-01-16', 'M002', 'B002', 1, 50, 750),
            (3, '2024-01-17', 'M001', 'B003', 3, 200, 3400),
            (4, '2024-01-18', 'M003', 'B001', 1, 0, 600);
    """)

    conn.commit()
    conn.close()

# 新增銷售記錄
def add_sale():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    sdate = input("請輸入銷售日期 (YYYY-MM-DD)：")
    if len(sdate) != 10 or sdate.count('-') != 2:
        print("=> 日期格式錯誤，應為 YYYY-MM-DD")
        conn.close()
        return

    mid = input("請輸入會員編號：")
    bid = input("請輸入書籍編號：")

    try:
        sqty = int(input("請輸入購買數量："))
        if sqty <= 0:
            print("=> 錯誤：數量必須為正整數，請重新輸入")
            conn.close()
            return
    except ValueError:
        print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
        conn.close()
        return

    try:
        sdiscount = int(input("請輸入折扣金額："))
        if sdiscount < 0:
            print("=> 錯誤：折扣金額不能為負數，請重新輸入")
            conn.close()
            return
    except ValueError:
        print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
        conn.close()
        return

    # 驗證會員ID是否存在
    cursor.execute("SELECT 1 FROM member WHERE mid = ?", (mid,))
    if not cursor.fetchone():
        print("=> 錯誤：會員編號或書籍編號無效")
        conn.close()
        return

    # 驗證書籍ID是否存在與庫存
    cursor.execute("SELECT bprice, bstock FROM book WHERE bid = ?", (bid,))
    result = cursor.fetchone()
    if not result:
        print("=> 錯誤：會員編號或書籍編號無效")
        conn.close()
        return

    bprice, bstock = result
    if sqty > bstock:
        print(f"=> 錯誤：書籍庫存不足 (現有庫存: {bstock})")
        conn.close()
        return

    stotal = bprice * sqty - sdiscount

    # 新增銷售紀錄
    cursor.execute('''
        INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (sdate, mid, bid, sqty, sdiscount, stotal))

    # 更新庫存
    cursor.execute('''
        UPDATE book SET bstock = bstock - ? WHERE bid = ?
    ''', (sqty, bid))

    conn.commit()
    conn.close()
    print(f"=> 銷售記錄已新增！(銷售總額: {stotal:,})")

# 顯示銷售報表
def show_report():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.sid, s.sdate, m.mname, b.btitle, b.bprice, s.sqty, s.sdiscount, s.stotal
        FROM sale s
        JOIN member m ON s.mid = m.mid
        JOIN book b ON s.bid = b.bid
        ORDER BY s.sid
    ''')

    sales = cursor.fetchall()

    for idx, row in enumerate(sales, start=1):
        print("=" * 50)
        print(f"銷售 #{idx}")
        print(f"銷售編號: {row[0]}")
        print(f"銷售日期: {row[1]}")
        print(f"會員姓名: {row[2]}")
        print(f"書籍標題: {row[3]}")
        print("-" * 50)
        print("單價\t數量\t折扣\t小計")
        print("-" * 50)
        print(f"{row[4]:,}\t{row[5]}\t{row[6]:,}\t{row[7]:,}")
        print("-" * 50)
        print(f"銷售總額: {row[7]:,}")
        print("=" * 50)

    conn.close()

# 更新銷售記錄
def update_sale():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.sid, m.mname, s.sdate FROM sale s
        JOIN member m ON s.mid = m.mid
        ORDER BY s.sid
    ''')
    sales = cursor.fetchall()

    print("\n======== 銷售記錄列表 ========")
    for i, row in enumerate(sales, start=1):
        print(f"{i}. 銷售編號: {row[0]} - 會員: {row[1]} - 日期: {row[2]}")
    print("================================")

    sid_input = input("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ")
    if not sid_input:
        return

    try:
        choice = int(sid_input)
        if choice < 1 or choice > len(sales):
            print("=> 錯誤：請輸入有效的數字")
            return
    except ValueError:
        print("=> 錯誤：請輸入有效的數字")
        return

    sid = sales[choice - 1][0]

    try:
        sdiscount = int(input("請輸入新的折扣金額："))
        if sdiscount < 0:
            print("=> 錯誤：折扣金額不能為負數")
            return
    except ValueError:
        print("=> 錯誤：折扣金額應為整數")
        return

    cursor.execute("SELECT sqty, bid FROM sale WHERE sid = ?", (sid,))
    row = cursor.fetchone()
    if row is None:
        print("=> 錯誤：找不到銷售記錄")
        return

    sqty, bid = row
    cursor.execute("SELECT bprice FROM book WHERE bid = ?", (bid,))
    bprice_row = cursor.fetchone()
    if bprice_row is None:
        print("=> 錯誤：找不到書籍資料")
        return

    bprice = bprice_row[0]
    stotal = bprice * sqty - sdiscount

    cursor.execute('''
        UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?
    ''', (sdiscount, stotal, sid))

    conn.commit()
    conn.close()
    print(f"=> 銷售編號 {sid} 已更新！(銷售總額: {stotal:,})")

# 刪除銷售記錄
def delete_sale():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.sid, m.mname, s.sdate FROM sale s
        JOIN member m ON s.mid = m.mid
        ORDER BY s.sid
    ''')
    sales = cursor.fetchall()

    print("\n======== 銷售記錄列表 ========")
    for i, row in enumerate(sales, start=1):
        print(f"{i}. 銷售編號: {row[0]} - 會員: {row[1]} - 日期: {row[2]}")
    print("================================")

    sid_input = input("請選擇要刪除的銷售編號 (輸入數字或按 Enter 取消): ")
    if not sid_input:
        return

    try:
        choice = int(sid_input)
        if choice < 1 or choice > len(sales):
            print("=> 錯誤：請輸入有效的數字")
            return
    except ValueError:
        print("=> 錯誤：請輸入有效的數字")
        return

    sid = sales[choice - 1][0]

    cursor.execute("DELETE FROM sale WHERE sid = ?", (sid,))
    conn.commit()
    conn.close()
    print(f"=> 銷售編號 {sid} 已刪除")

# 主選單
def main():
    init_db()

    while True:
        print("\n***************選單***************")
        print("1. 新增銷售記錄")
        print("2. 顯示銷售報表")
        print("3. 更新銷售記錄")
        print("4. 刪除銷售記錄")
        print("5. 離開")
        print("**********************************")
        choice = input("請選擇操作項目(Enter 離開)：")

        if choice == '1':
            add_sale()
        elif choice == '2':
            show_report()
        elif choice == '3':
            update_sale()
        elif choice == '4':
            delete_sale()
        elif choice == '5' or choice == '':
            print("再見！")
            break
        else:
            print("=> 請輸入有效的選項（1-5）")

if __name__ == '__main__':
    main()
