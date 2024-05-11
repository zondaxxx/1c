import csv
import sys
import sqlite3
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox, QApplication, QMainWindow, QPushButton, QDialog, QTabWidget

import design

class DatabaseManager:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка при выполнении запроса: {e}") # вывод ошибки при ошибочном выполнении.
            return []

class TableSetup:
    def __init__(self, table_widget):
        self.table_widget = table_widget

    def set_up_table(self, data, headers):
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setRowCount(len(data))
        self.table_widget.setHorizontalHeaderLabels(headers)

        for row in range(self.table_widget.rowCount()):
            for column in range(self.table_widget.columnCount()):
                item = QTableWidgetItem(str(data[row][column]))
                self.table_widget.setItem(row, column, item)

class App(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db_manager = DatabaseManager('main.sqlite')
        self.open_magaz_file()
        self.action_savecsv.triggered.connect(self.save_csv)
        self.action_dobavit_dvig.triggered.connect(self.add_dvig_entry)
        self.save.clicked.connect(self.save_to_db)
        

    def open_magaz_file(self):
        self.set_up_table_magaz()
        self.set_up_table_product()
        self.set_up_table_dvig()

    def set_up_table_magaz(self):
        data = self.db_manager.execute_query('SELECT * FROM "Shops"')
        headers = ["ID Магазина", "Район","Адрес"]
        table_setup = TableSetup(self.table_magaz)
        table_setup.set_up_table(data, headers)

    def set_up_table_product(self):
        data = self.db_manager.execute_query('SELECT * FROM "Products"')
        headers = ["Артикул", "Отдел", "Наименование товара", "Ед. Изм", "Количество", "Поставщик"]
        table_setup = TableSetup(self.table_product)
        table_setup.set_up_table(data, headers)

    def set_up_table_dvig(self):
        data = self.db_manager.execute_query('SELECT * FROM "Logistic"')
        headers = ["ID операции", "Дата", "ID Магазина", "Артикул", "Количество упаковок, шт.", "Тип операции", "Цена руб./шт."]
        table_setup = TableSetup(self.table_dvig)
        table_setup.set_up_table(data, headers)

    def save_csv(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save as CSV", "", "CSV files (*.csv)", options=QFileDialog.DontUseNativeDialog)
        if file_name:
            self.save_table_to_csv(file_name)

    def save_table_to_csv(self, file_name):
        table_widget = self.get_current_table_widget()
        if table_widget:
            with open(file_name, 'w', newline='', encoding='utf-8-sig') as csv_file:
                writer = csv.writer(csv_file)
                headers = []
                for column in range(table_widget.columnCount()):
                    headers.append(table_widget.horizontalHeaderItem(column).text())
                writer.writerow(headers)

                for row in range(table_widget.rowCount()):
                    row_data = [table_widget.item(row, column).text() for column in range(table_widget.columnCount())]
                    writer.writerow(row_data)

    def get_current_table_widget(self):

        tab_index = self.tabWidget.currentIndex()

        if tab_index == 0:
            return self.table_magaz
        elif tab_index == 1:
            return self.table_product
        elif tab_index == 2:
            return self.table_dvig
        else:
            print(f"Unknown tab index: {tab_index}")
            return None

    def add_dvig_entry(self):
        dialog = AddDvigEntryDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            query = "INSERT INTO 'Logistic' VALUES (?,?,?,?,?,?,?)"
            self.db_manager.execute_query(query, tuple(data))
            self.set_up_table_dvig()

    def save_to_db(self):
        try:
            self.db_manager.execute_query("BEGIN TRANSACTION")
            self.save_table_to_db(self.table_magaz, "Shops")
            self.save_table_to_db(self.table_product, "Products")
            self.save_table_to_db(self.table_dvig, "Logistic")
            self.db_manager.execute_query("COMMIT")
            QMessageBox.information(self, "Success", "Data saved to database successfully")
        except sqlite3.Error as e:
            self.db_manager.execute_query("ROLLBACK")
            QMessageBox.critical(self, "Error", f"Error saving data to database: {e}")

    

    def save_table_to_db(self, table_widget, table_name):
        query = f"DELETE FROM {table_name}"
        self.db_manager.execute_query(query)
        for row in range(table_widget.rowCount()):
            data = []
            for column in range(table_widget.columnCount()):
                item = table_widget.item(row, column)
                data.append(item.text())
            query = f"INSERT INTO {table_name} VALUES ({','.join(['?']*len(data))})"
            self.db_manager.execute_query(query, tuple(data))

            
    

class AddDvigEntryDialog(QDialog): # Диалоговое окно для добавления в движение товаров
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Добавить новый объект в движение товара")
        self.layout = QtWidgets.QVBoxLayout(self)

        self.form_layout = QtWidgets.QFormLayout()
        self.layout.addLayout(self.form_layout)

        self.id_operacii_label = QtWidgets.QLabel("ID операции")
        self.id_operacii_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.id_operacii_label, self.id_operacii_edit)

        self.data_label = QtWidgets.QLabel("Дата")
        self.data_edit = QtWidgets.QDateEdit()
        self.form_layout.addRow(self.data_label, self.data_edit)

        self.id_magazina_label = QtWidgets.QLabel("ID Магазина")
        self.id_magazina_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.id_magazina_label, self.id_magazina_edit)

        self.articul_label = QtWidgets.QLabel("Артикул")
        self.articul_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.articul_label, self.articul_edit)

        self.kol_upakovok_label = QtWidgets.QLabel("Количество упаковок, шт.")
        self.kol_upakovok_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.kol_upakovok_label, self.kol_upakovok_edit)

        self.tip_operacii_label = QtWidgets.QLabel("Тип операции")
        self.tip_operacii_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.tip_operacii_label, self.tip_operacii_edit)

        self.cena_rub_label = QtWidgets.QLabel("Цена руб./шт.")
        self.cena_rub_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.cena_rub_label, self.cena_rub_edit)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        data = [
            self.id_operacii_edit.text(),
            self.data_edit.date().toString("yyyy-MM-dd"),
            self.id_magazina_edit.text(),
            self.articul_edit.text(),
            self.kol_upakovok_edit.text(),
            self.tip_operacii_edit.text(),
            self.cena_rub_edit.text()
        ]
        return data

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()