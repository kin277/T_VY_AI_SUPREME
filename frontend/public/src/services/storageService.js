// Sử dụng IndexedDB để lưu hàng nghìn tin nhắn không lo tràn dung lượng
export class StorageService {
    constructor() {
        this.dbName = 'AISupremeDB';
        this.initDB();
    }

    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 1);
            request.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('messages')) {
                    db.createObjectStore('messages', { keyPath: 'id', autoIncrement: true });
                }
            };
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject('Không thể mở cơ sở dữ liệu');
        });
    }

    async saveMessage(chatId, role, text) {
        const db = await this.initDB();
        const tx = db.transaction('messages', 'readwrite');
        const store = tx.objectStore('messages');
        store.add({ chatId, role, text, timestamp: new Date().toISOString() });
    }
}