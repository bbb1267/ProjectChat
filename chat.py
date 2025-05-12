import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, font

class SimpleChatApp:
    def __init__(self):
        self.PORT = 5555
        self.host_socket = None
        self.client_socket = None
        self.connection = None
        self.nickname = ""
        self.peer_nickname = ""

        self.root = tk.Tk()
        self.root.title("Simple Chat")
        self.root.geometry("500x600")
        self.root.configure(bg='#333333')  

        self.font_normal = font.Font(family="Arial", size=10)
        self.font_bold = font.Font(family="Arial", size=10, weight="bold")

        button_style = {
            'bg': '#555555',
            'fg': 'white',
            'activebackground': '#777777',
            'activeforeground': 'white',
            'font': self.font_bold,
            'relief': tk.RAISED,
            'borderwidth': 2
        }

        self.top_frame = tk.Frame(self.root, bg='#333333')
        self.top_frame.pack(pady=10)
        
        self.host_btn = tk.Button(self.top_frame, text="Создать чат", 
                                command=self.start_host, **button_style)
        self.host_btn.pack(side=tk.LEFT, padx=10)
        
        self.join_btn = tk.Button(self.top_frame, text="Присоединиться", 
                                command=self.start_client, **button_style)
        self.join_btn.pack(side=tk.LEFT, padx=10)

        self.chat_frame = tk.Frame(self.root, bg='#333333')
        self.chat_frame.pack(padx=10, pady=5, expand=True, fill=tk.BOTH)
        
        self.chat_area = scrolledtext.ScrolledText(
            self.chat_frame,
            state='disabled',
            bg='#444444',
            fg='white',
            insertbackground='white',
            font=self.font_normal,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.chat_area.pack(expand=True, fill=tk.BOTH)

        self.bottom_frame = tk.Frame(self.root, bg='#333333')
        self.bottom_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.msg_entry = tk.Entry(
            self.bottom_frame,
            bg='#555555',
            fg='white',
            insertbackground='white',
            font=self.font_normal,
            relief=tk.SUNKEN,
            borderwidth=3
        )
        self.msg_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.msg_entry.bind("<Return>", self.send_message)
        
        self.send_btn = tk.Button(
            self.bottom_frame,
            text="Отправить",
            command=self.send_message,
            **button_style
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(10, 0))

        self.status_bar = tk.Label(
            self.root,
            text="Статус: Не подключено",
            bg='#333333',
            fg='white',
            font=self.font_normal,
            anchor=tk.W,
            relief=tk.SUNKEN,
            bd=1
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
    
    def start_host(self):
        self.nickname = simpledialog.askstring("Никнейм", "Введите ваш никнейм:", parent=self.root)
        if not self.nickname:
            return
            
        try:
            self.host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.host_socket.bind(('0.0.0.0', self.PORT))
            self.host_socket.listen(1)
            
            self.update_status("Ожидание подключения...")
            self.display_message("[Система] Чат создан. Ожидаем подключения...")
            
            accept_thread = threading.Thread(target=self.accept_connection, daemon=True)
            accept_thread.start()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать чат: {e}")
    
    def accept_connection(self):
        try:
            self.connection, addr = self.host_socket.accept()
            self.peer_nickname = self.connection.recv(1024).decode('utf-8')
            self.connection.send(self.nickname.encode('utf-8'))
            
            self.update_status(f"Подключено к {self.peer_nickname}")
            self.display_message(f"[Система] Вы подключены к {self.peer_nickname}")
            
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
        except Exception as e:
            self.display_message(f"[Система] Ошибка подключения: {e}")
    
    def start_client(self):
        self.nickname = simpledialog.askstring("Никнейм", "Введите ваш никнейм:", parent=self.root)
        if not self.nickname:
            return
            
        host = simpledialog.askstring("Подключение", "Введите IP сервера:", parent=self.root)
        if not host:
            return
            
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, self.PORT))
            self.connection = self.client_socket
            
            self.client_socket.send(self.nickname.encode('utf-8'))
            self.peer_nickname = self.client_socket.recv(1024).decode('utf-8')
            
            self.update_status(f"Подключено к {self.peer_nickname}")
            self.display_message(f"[Система] Вы подключены к {self.peer_nickname}")
            
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
    
    def receive_messages(self):
        while True:
            try:
                message = self.connection.recv(1024).decode('utf-8')
                if not message:
                    break
                    
                self.display_message(message)
            except:
                self.display_message("[Система] Соединение разорвано")
                self.cleanup_connection()
                break
    
    def send_message(self, event=None):
        message = self.msg_entry.get()
        if message and self.connection:
            try:
                full_msg = f"{self.nickname}: {message}"
                self.connection.send(full_msg.encode('utf-8'))
                self.display_message(f"Вы: {message}")
                self.msg_entry.delete(0, tk.END)
            except Exception as e:
                self.display_message(f"[Система] Не удалось отправить сообщение: {e}")
                self.cleanup_connection()
    
    def display_message(self, message):
        self.chat_area.config(state='normal')

        if message.startswith("Вы:"):
            tag = "you"
        elif message.startswith(self.peer_nickname + ":"):
            tag = "peer"
        else:
            tag = "system"

        self.chat_area.tag_config("you", foreground="#4CAF50")
        self.chat_area.tag_config("peer", foreground="#2196F3")
        self.chat_area.tag_config("system", foreground="#FF9800")
        
        self.chat_area.insert(tk.END, message + "\n", tag)
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)
    
    def update_status(self, text):
        self.status_bar.config(text=f"Статус: {text}")
    
    def cleanup_connection(self):
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
        
        if self.host_socket:
            try:
                self.host_socket.close()
            except:
                pass
            self.host_socket = None
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        self.update_status("Не подключено")
    
    def on_close(self):
        self.cleanup_connection()
        self.root.destroy()

if __name__ == "__main__":
    SimpleChatApp()