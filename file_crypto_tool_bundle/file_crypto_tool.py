import os
import time
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox

# ─── 설정 ─────────────────────────────────────────────────────────────────────────
MAGIC_HEADER = b"FILESEC"   # 복호화 성공 판별용 마법 바이트
LOG_FILE     = "encryption_log.txt"

# ─── 키 스트림 생성: SHA256(password) → 32바이트 → 키 스트림 반복 ────────────────────
def make_keystream(key: str, length: int) -> bytes:
    digest = hashlib.sha256(key.encode()).digest()
    return (digest * (length // len(digest) + 1))[:length]

# ─── XOR 암/복호화 + 헤더 처리 ────────────────────────────────────────────────────
def transform(data: bytes, key: str, encrypt: bool) -> bytes:
    if encrypt:
        data = MAGIC_HEADER + data
    ks = make_keystream(key, len(data))
    out = bytes(a ^ b for a, b in zip(data, ks))
    if not encrypt:
        # 복호화 후 MAGIC_HEADER 복원 검사
        raw = bytes(a ^ b for a, b in zip(out, ks))
        if not raw.startswith(MAGIC_HEADER):
            return None
        out = raw[len(MAGIC_HEADER):]
    return out

# ─── 단일 파일 처리 ───────────────────────────────────────────────────────────────
def process_file(path: str, key: str, encrypt: bool, overwrite: bool):
    try:
        with open(path, "rb") as f:
            data = f.read()
        result = transform(data, key, encrypt)
        if result is None:
            messagebox.showerror("복호화 실패", f"잘못된 키: {os.path.basename(path)}")
            return False

        # 출력 경로 결정
        if encrypt:
            out_path = path if overwrite else path + ".enc"
        else:
            base = path[:-4] if path.endswith(".enc") else path
            out_path = base if overwrite else base + ".dec"

        with open(out_path, "wb") as f:
            f.write(result)

        log_action("Encrypted" if encrypt else "Decrypted", out_path)
        return True

    except Exception as e:
        messagebox.showerror("오류", f"{e}")
        return False

# ─── 디렉터리 전체 재귀 처리 ───────────────────────────────────────────────────━
def process_directory(folder: str, key: str, encrypt: bool, overwrite: bool):
    for root, dirs, files in os.walk(folder):
        for name in files:
            fp = os.path.join(root, name)
            if encrypt and not name.endswith(".enc"):
                process_file(fp, key, True, overwrite)
            elif not encrypt and name.endswith(".enc"):
                process_file(fp, key, False, overwrite)

# ─── 로그 기록 ─────────────────────────────────────────────────────────────────────
def log_action(action: str, path: str):
    with open(LOG_FILE, "a", encoding="utf-8") as lf:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        lf.write(f"{ts} - {action}: {path}\n")

# ─── GUI ────────────────────────────────────────────────────────────────────────────
def select_path():
    if var_mode.get() == "file":
        p = filedialog.askopenfilename()
    else:
        p = filedialog.askdirectory()
    entry_path.delete(0, tk.END)
    entry_path.insert(0, p)

def start():
    path = entry_path.get().strip()
    key  = entry_key.get().strip()
    encrypt = (var_enc.get() == "encrypt")
    overwrite = var_ovr.get()

    if not path or not key:
        messagebox.showwarning("입력 부족", "경로와 키를 모두 입력하세요.")
        return

    if os.path.isdir(path):
        process_directory(path, key, encrypt, overwrite)
        messagebox.showinfo("완료", "디렉터리 작업 완료")
    else:
        ok = process_file(path, key, encrypt, overwrite)
        if ok:
            messagebox.showinfo("완료", "파일 처리 완료")

root = tk.Tk()
root.title("AES 없이 순수 파이썬 암/복호화 툴")
root.configure(bg="black")
root.geometry("480x320")

tk.Label(root, text="파일/폴더 경로:", bg="black", fg="white").pack(pady=(10,0))
entry_path = tk.Entry(root, width=60); entry_path.pack(padx=10)
tk.Button(root, text="찾아보기", command=select_path, bg="gray", fg="white").pack(pady=5)

tk.Label(root, text="키(비밀번호):", bg="black", fg="white").pack(pady=(10,0))
entry_key = tk.Entry(root, show="*"); entry_key.pack(padx=10)

# 파일 vs 폴더
var_mode = tk.StringVar(value="file")
frm1 = tk.Frame(root, bg="black")
tk.Radiobutton(frm1, text="파일", variable=var_mode, value="file", bg="black", fg="white").pack(side="left", padx=5)
tk.Radiobutton(frm1, text="폴더", variable=var_mode, value="folder", bg="black", fg="white").pack(side="left", padx=5)
frm1.pack(pady=5)

# 암호화 vs 복호화
var_enc = tk.StringVar(value="encrypt")
frm2 = tk.Frame(root, bg="black")
tk.Radiobutton(frm2, text="암호화", variable=var_enc, value="encrypt", bg="black", fg="white").pack(side="left", padx=5)
tk.Radiobutton(frm2, text="복호화", variable=var_enc, value="decrypt", bg="black", fg="white").pack(side="left", padx=5)
frm2.pack(pady=5)

# 덮어쓰기 옵션
var_ovr = tk.BooleanVar()
tk.Checkbutton(root, text="원본 덮어쓰기", variable=var_ovr, bg="black", fg="white").pack(pady=5)

tk.Button(root, text="실행", command=start, bg="gray", fg="white").pack(pady=15)

root.mainloop()
