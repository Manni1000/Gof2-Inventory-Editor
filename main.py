import sys
import os
import struct
from tqdm import tqdm
import copy
from PIL import ImageQt

from PyQt6.QtCore import Qt, QSize, QObject, QDir
from PyQt6.QtGui import QPixmap, QPalette
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QScrollArea,
                             QGridLayout, QLineEdit, QListWidget, QListWidgetItem, QHBoxLayout,
                             QFrame, QPushButton, QGroupBox, QSpinBox, QDoubleSpinBox, QStackedWidget,
                             QGraphicsOpacityEffect, QAbstractSpinBox, QMessageBox, QDialog,
                             QSizePolicy, QCheckBox, QInputDialog, QComboBox, QFileDialog,
                             QLineEdit, QSpinBox)
from PyQt6.QtWidgets import QTabWidget

from gof2Installation import Gof2Installation


from itemdb import itemdb
#from item_editing import (find_item_data_positions, read_item_data, read_money_amount, save_money_amount, save_item_data, itemsOrginal)
items = []
saveloaded = False

DEFAULT_SAVES_FOLDERS = {
    "nt": os.path.expandvars("%USERPROFILE%\\AppData\\Roaming\\Galaxy on Fire 2 Full HD")
}

DEFAULT_INSTALLATION_FOLDERS = {
    "nt": os.path.expandvars("%ProgramFiles(x86)%\\Steam\\steamapps\\common\\Galaxy On Fire 2 HD")
}


###################
#acual item edeting
###################
itemsOrginal = []

def find_item_data_positions(file_bytes, num_items):
    possible_positions = []
    for i in range(len(file_bytes) - 4):
        possible_item_count = struct.unpack("I", file_bytes[i:i + 4])[0]
        if possible_item_count == num_items:
            pattern_found = True
            item_ids = set()
            for j in range(num_items):
                spacer_position = i + 4 + (13 * j) + 12
                #i think its a spacer. normaly it is 00 but somtimes 04 and maby others values idk
                if spacer_position >= len(file_bytes) or file_bytes[spacer_position] not in [0, 4]:

                    pattern_found = False
                    break
                item_id = struct.unpack("I", file_bytes[i + 4 + (13 * j):i + 4 + (13 * j) + 4])[0]
                if item_id > 196:
                    pattern_found = False
                    break
                if item_id in item_ids:
                    pattern_found = False
                    break
                item_ids.add(item_id)
            if pattern_found:
                #print(f"Pattern found at position: {i}")
                possible_positions.append(i)
            #else:
                #print(f"Pattern not found at position: {i}")
        #else:
            #print(f"Item count not matched at position: {i}")
    print("possible positions: " + str(len(possible_positions)))
    return possible_positions

def read_item_data(file_in, num_items, item_data_position=None):
    items = []
    global itemsOrginal
    with open(file_in, "rb") as file_save:
        file_bytes = file_save.read()
        item_data_positions = find_item_data_positions(file_bytes, num_items)
        if item_data_positions:
            if item_data_position is None:
                item_data_position = item_data_positions[0]
            file_save.seek(item_data_position)
            quantity_of_items = struct.unpack("I", file_save.read(4))[0]
            print('number of items: ' + str(quantity_of_items))
            for i in range(quantity_of_items):
                item_ID = struct.unpack("I", file_save.read(4))[0]
                quantity_of_this_item = struct.unpack("I", file_save.read(4))[0]
                item_price = struct.unpack("I", file_save.read(4))[0]
                file_save.seek(1, 1)
                items.append((item_ID, quantity_of_this_item, item_price))
                itemsOrginal = copy.deepcopy(items)
        else:
            raise ValueError("Could not find item data in the file")
    return items, item_data_positions

def read_money_amount(file_in):
    money_offset = 0x0000008B
    with open(file_in, "rb") as file_save:
        file_save.seek(money_offset)
        money_bytes = file_save.read(4)
        money_amount = struct.unpack("<I", money_bytes)[0]
    return money_amount

def save_money_amount(file_in, new_money_amount):
    money_offset = 0x0000008B
    with open(file_in, "r+b") as file_save:
        file_save.seek(money_offset)
        money_bytes = struct.pack("<I", int(new_money_amount))

        file_save.write(money_bytes)

def save_item_data(file_in, items):
    global retry_selector
    items_old = itemsOrginal
    print(items)
    print(items_old)
    print("acualy saving")

    quantity_of_items = len(items)
    file_out = file_in

    # Rename the old file with the "_old" suffix
    os.rename(file_in, file_in + "_old")

    with open(file_in + "_old", "rb") as f:
        file_bytes = f.read()
        # Get the selected position from the retry_selector
        selected_position = int(retry_selector.currentText())
        start_of_item_data = selected_position
        end_of_item_data = start_of_item_data + (13 * len(items_old)) + 4
        end_of_file = len(file_bytes)

        # Copy the data before the item data to the new file
        with open(file_out, "wb") as f2:
            f2.write(file_bytes[:start_of_item_data])

            # Add number of items
            f2.write(struct.pack("I", quantity_of_items))

            # Write the updated item data from the list
            for item in items:
                f2.write(struct.pack("III", *item) + b"\x00")

            # Copy the data after the item data to the
            f2.write(file_bytes[end_of_item_data:end_of_file])



#################
# gui code
#################

folder_path = DEFAULT_SAVES_FOLDERS.get(os.name, None)
if folder_path and not os.path.isdir(folder_path):
    folder_path = None

default_installation_path = DEFAULT_INSTALLATION_FOLDERS.get(os.name, None)
if default_installation_path and not os.path.isdir(default_installation_path):
    default_installation_path = None

gof2_installation = (None if default_installation_path is None
                     else Gof2Installation(default_installation_path))

app = QApplication(sys.argv)
main_window = QMainWindow()
main_window.setWindowTitle("Inventory Editor")
main_window.setMinimumSize(QSize(800, 600))



def get_loose_items_count():
    num_loose_items, ok = QInputDialog.getInt(None, "Loose Items", "Enter the number of loose items:", 0, 0, 1000, 1)
    if ok:
        return num_loose_items
    else:
        return None

def on_select_save_file_button_clicked():
    global saveloaded, save_path, num_loose_items
    num_loose_items = get_loose_items_count()
    if num_loose_items is None:
        return  # User canceled the input dialog

    # Continue with the save file selection and processing
    # ...

select_save_file_button = QPushButton("Select Save File")
select_save_file_button.clicked.connect(on_select_save_file_button_clicked)

def create_money_box():
    global money_display_label, money_spinbox
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setLineWidth(2)

    # Set the yellow border for the frame
    #frame.setStyleSheet("border: 2px solid yellow;")

    money_layout = QHBoxLayout(frame)

    money_label = QLabel("Money:")
    money_layout.addWidget(money_label)

    money_stacked_widget = QStackedWidget()
    money_layout.addWidget(money_stacked_widget)

    money_display_label = QLabel(f"${initial_money:.2f}")
    money_stacked_widget.addWidget(money_display_label)

    money_spinbox = QDoubleSpinBox()
    money_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    money_spinbox.setPrefix("$")
    money_spinbox.setRange(0, 1e12)
    money_spinbox.setValue(initial_money)
    money_stacked_widget.addWidget(money_spinbox)

    def on_money_value_changed(value):
        global initial_money
        initial_money = value
        money_display_label.setText(f"${initial_money:.2f}")
        refresh_inventory()

    money_spinbox.valueChanged.connect(on_money_value_changed)

    def on_money_display_label_clicked():
        money_stacked_widget.setCurrentIndex(1)
        money_spinbox.setFocus()
        money_spinbox.selectAll()

    money_display_label.mousePressEvent = lambda event: on_money_display_label_clicked()

    def on_money_spinbox_editing_finished():
        money_stacked_widget.setCurrentIndex(0)

    money_spinbox.editingFinished.connect(on_money_spinbox_editing_finished)

    return frame


def load_image(item_id):
    if gof2_installation is None:
        return QPixmap()
    try:
        texture = gof2_installation.item_icons().get_image(item_id)
    except Exception as ex:
        print(f"Failed to load item icon for item {item_id}: {ex}")
        return QPixmap()
    
    pixmap = ImageQt.toqpixmap(texture)
    return pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)

def on_delete_button_clicked():
    button = app.sender()
    item_widget = button.parent()
    layout_item = item_widget.layout().itemAt(1)
    item_name = layout_item.widget().text()

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle("Confirm Remove")
    msg_box.setText(f"Are you sure you want to remove {item_name} from your inventory?")

    remove_all_checkbox = QCheckBox("Remove all items")
    msg_box.setCheckBox(remove_all_checkbox)

    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QMessageBox.StandardButton.No)
    button_pressed = msg_box.exec()

    if button_pressed == QMessageBox.StandardButton.Yes:
        global items
        item_id = [key for key, value in itemdb.items() if value == item_name][0]

        if remove_all_checkbox.isChecked():
            items = []
        else:
            for index, (id, count, price) in enumerate(items):
                if id == item_id:
                    items.pop(index)
                    break

        refresh_inventory()

def create_item_widget(item_id, item_name, item_count=None):
    item_widget = QWidget()
    item_widget.setFixedHeight(50)
    grid = QGridLayout(item_widget)
    grid.setAlignment(Qt.AlignmentFlag.AlignTop)

    item_image_label = QLabel()
    item_image_label.setPixmap(load_image(item_id))
    grid.addWidget(item_image_label, 0, 0)

    item_name_label = QLabel(item_name)
    grid.addWidget(item_name_label, 0, 1)

    if item_count is not None:
        count_stacked_widget = QStackedWidget()
        grid.addWidget(count_stacked_widget, 0, 2)

        item_count_label = QLabel(f"Count: {item_count}")
        count_stacked_widget.addWidget(item_count_label)

        count_spinbox = QSpinBox()
        count_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        count_spinbox.setRange(0, 999)
        count_spinbox.setValue(item_count)
        count_stacked_widget.addWidget(count_spinbox)

        def on_count_value_changed():
            value = count_spinbox.value()  # Get the value from the spinbox
            item_id = [key for key, value in itemdb.items() if value == item_name][0]
            for index, (id, count, price) in enumerate(items):
                if id == item_id:
                    items[index] = (id, value, price)
                    break
            count_stacked_widget.widget(0).setText(f"Count: {value}")  # Update item count label


        count_spinbox.editingFinished.connect(on_count_value_changed)


        def on_item_count_label_clicked():
            count_stacked_widget.setCurrentIndex(1)
            count_spinbox.setFocus()
            count_spinbox.selectAll()

        item_count_label.mousePressEvent = lambda event: on_item_count_label_clicked()

        def on_count_spinbox_editing_finished():
            count_stacked_widget.setCurrentIndex(0)

        count_spinbox.editingFinished.connect(on_count_spinbox_editing_finished)

        delete_button = QPushButton("Remove")
        delete_button.setObjectName(f"{item_name}_delete_button")
        grid.addWidget(delete_button, 0, 3)
        delete_button.clicked.connect(on_delete_button_clicked)

    return item_widget

def add_item_to_inventory(item_name):
    global items, saveloaded
    if not saveloaded:
        return
    item_id = [key for key, value in itemdb.items() if value == item_name][0]

    item_exists = False
    for index, (id, count, price) in enumerate(items):
        if id == item_id:
            item_exists = True
            items[index] = (id, count + 1, price)
            break

    if not item_exists:
        items.append((item_id, 1, 4))

    refresh_inventory()

def refresh_inventory():
    global inventory_layout, saveloaded
    if not saveloaded:
        return
    for i in reversed(range(inventory_layout.count())):
        inventory_layout.itemAt(i).widget().setParent(None)

    inventory_height = max(600, len(items) * 50 + 50) # calculate the height of the inventory list based on the number of items

    inventory_widget.setMinimumHeight(inventory_height) # set the minimum height of the inventory widget

    print(initial_money)

    refresh_itemdb_list("")


    # Print the items list in the console
    print(items)


central_widget = QWidget(main_window)
main_window.setCentralWidget(central_widget)

initial_money = 100.0  # Set the initial value of money

# Left side layout
left_layout = QVBoxLayout()

search_field = QLineEdit()
left_layout.addWidget(search_field)

left_list = QListWidget()
left_layout.addWidget(left_list)

item_icons = []

def refresh_itemdb_list(searchText):
    left_list.clear()
    for icon in item_icons:
        icon.close()
    for item_id, item_name in itemdb.items():
        if not searchText or searchText.lower() in item_name.lower():
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(200, 50))
            item_widget = create_item_widget(item_id, item_name)
            left_list.addItem(list_item)
            left_list.setItemWidget(list_item, item_widget)

refresh_itemdb_list("")
search_field.textChanged.connect(refresh_itemdb_list)

def on_left_list_item_clicked(item):
    item_widget = left_list.itemWidget(item)
    layout_item = item_widget.layout().itemAt(1)
    item_name = layout_item.widget().text()

    # Add the item to the inventory or increment the count
    global items
    item_id = [key for key, value in itemdb.items() if value == item_name][0]

    item_exists = False
    for index, (id, count, price) in enumerate(items):
        if id == item_id:
            item_exists = True
            items[index] = (id, count + 1, price)
            break

    if not item_exists:
        items.append((item_id, 1, 4))

    refresh_inventory()


left_list.itemClicked.connect(on_left_list_item_clicked)

# Wrap the left side layout with a QGroupBox (ItemSelectorBox)
left_group_box = QGroupBox("Search and Add Items")
left_group_box.setLayout(left_layout)

# Right side layout
inventory_scroll_area = QScrollArea(main_window)
inventory_scroll_area.setWidgetResizable(True)
inventory_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
inventory_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

inventory_widget = QWidget()
inventory_scroll_area.setWidget(inventory_widget)

# Add QVBoxLayout to inventory_widget
#inventory_layout = QVBoxLayout(inventory_widget)
inventory_layout = QVBoxLayout(inventory_widget)



inventory_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

refresh_inventory()

# Set minimum height for the inventory_widget to avoid empty space
inventory_widget.setMinimumHeight(600)

# Wrap the inventory_widget with a QGroupBox (ItemInventoryBox)
right_group_box = QGroupBox("Inventory")
right_group_box.setLayout(QVBoxLayout())
right_group_box.layout().addWidget(inventory_scroll_area)

# Create a QHBoxLayout for the ItemEditor
item_editor_layout = QHBoxLayout()
item_editor_layout.addWidget(left_group_box)
item_editor_layout.addWidget(right_group_box)

# Create a QGroupBox for the ItemEditor and set red edges
item_editor_group_box = QGroupBox("")
item_editor_group_box.setLayout(item_editor_layout)
#item_editor_group_box.setStyleSheet("QGroupBox { border: 2px solid red; }")

# Add the ItemEditor and the money box to the main layout
#inilise the main layout
main_layout = QVBoxLayout()

#create taps

tab_widget = QTabWidget()

tab1 = QWidget()
tab1_layout = QVBoxLayout()
tab1.setLayout(tab1_layout)

tab2 = QWidget()
tab2_layout = QVBoxLayout()
tab2.setLayout(tab2_layout)

#create box wher all stuff of the tap is
standardInvEdit = QGroupBox("")
standardInvEdit_layout = QVBoxLayout()
standardInvEdit.setLayout(standardInvEdit_layout)
standardInvEdit.setStyleSheet("QGroupBox { border: 0px solid; }")
tab1_layout.addWidget(standardInvEdit)



#select folder stuff
saveLoadIsPossible = False
# Import additional classes
from PyQt6.QtWidgets import QComboBox, QFileDialog, QLineEdit, QSpinBox

# Create the "saveselectorbox"
saveselectorbox = QGroupBox("")
saveselector_layout = QHBoxLayout(saveselectorbox)

# Create the "installationFolderButton" and add it to the layout
installationFolderButton = QPushButton("Select GOF2 Installation")
saveselector_layout.addWidget(installationFolderButton)

# Create the "savefolderbutton" and add it to the layout
savefolderbutton = QPushButton("Select Save Folder")
saveselector_layout.addWidget(savefolderbutton)

# Create the "savedropdownselector" and add it to the layout
savedropdownselector = QComboBox()
saveselector_layout.addWidget(savedropdownselector)

# Create the "loseitemsnumber" and add it to the layout
loseitemsnumber = QSpinBox()
loseitemsnumber.setRange(0, 1000)
loseitemsnumber.setSuffix(" Loose Items")
saveselector_layout.addWidget(loseitemsnumber)

def refresh_save_files():
    if folder_path:
        nonSaveNames = ["preview", "GoF2.ini", "options"]
        gameSaveNames = []

        for file in os.listdir(folder_path):
            if not any(word in file for word in nonSaveNames):
                gameSaveNames.append(file)

        savedropdownselector.clear()
        savedropdownselector.addItems(gameSaveNames)

if folder_path:
    refresh_save_files()

def on_save_button_clicked():
    global saveloaded, save_path, items, initial_money
    if saveloaded:
        print("Saving items")
        # Save the item database to the external file
        #save_path = os.path.join(folder_path, savedropdownselector.currentText())
        save_item_data(file_in = save_path, items=list(items))
        save_money_amount(file_in = save_path, new_money_amount = initial_money)
    else:
        error_box = QMessageBox()
        error_box.setWindowTitle("Cannot save items")
        error_box.setText("Please load a valid save file and enter the number of loose items.")
        error_box.exec()

def on_load_save_button_clicked():
    global saveloaded, save_path, num_loose_items, folder_path, items, initial_money, items
    if saveLoadIsPossible == True:
        print("Loading save")
        # Load the item database from the external file
        save_path = os.path.join(folder_path, savedropdownselector.currentText())
        num_loose_items = loseitemsnumber.value()
        print(f"Loading save from {save_path} with {num_loose_items} loose items.")
        # Load the item db from the save file and update the inventory accordingly
        try:
            items, item_data_positions = read_item_data(file_in=save_path, num_items=num_loose_items)
        except ValueError as e:
            print(f"cumError: {e}")
            return

        # Update the drop-down menu with the positions
        update_retry_selector(item_data_positions)
        initial_money = read_money_amount(file_in = save_path)
        money_display_label.setText(f"${initial_money:.2f}")
        money_spinbox.setValue(initial_money)
        saveloaded = True
        refresh_inventory()
    else:
        error_box = QMessageBox()
        error_box.setWindowTitle("Cannot load save")
        error_box.setText("Please load a valid save file and enter the number of loose items.")
        error_box.exec()

#Create the "loadSave" button adn add it to the layout
load_save_button = QPushButton("Load Save")
load_save_button.setStyleSheet("background-color: yellow; color: black")
load_save_button.clicked.connect(on_load_save_button_clicked)
saveselector_layout.addWidget(load_save_button)

def on_load_assets_button_clicked():
    global gof2_installation
    qt_path = QFileDialog.getExistingDirectory(None, "Select GOF2 Installation Folder", default_installation_path)
    installation_path = QDir.toNativeSeparators(qt_path)
    error_box = QMessageBox()
    error_box.setWindowTitle("Invalid GOF2 Installation")
    if not os.path.isdir(installation_path):
        error_box.setText("The directory does not exist.")
        error_box.exec()
        return
    try:
        new_installation = Gof2Installation(installation_path)
    except Exception as ex:
        error_box.setText(f"{type(ex)}: {ex}")
        error_box.exec()
        return
    if gof2_installation:
        gof2_installation.close()
    gof2_installation = new_installation
    refresh_itemdb_list("")
    refresh_inventory()

#Create the "loadAssets" button and add it to the layout
installationFolderButton.clicked.connect(on_load_assets_button_clicked)

def update_retry_selector(item_data_positions):
    retry_selector.clear()
    for position in item_data_positions:
        retry_selector.addItem(str(position))
    retry_selector.setEnabled(True)

def on_retry_selector_changed():
    global num_loose_items, save_path, items
    selected_position = int(retry_selector.currentText())
    items, _ = read_item_data(file_in=save_path, num_items=num_loose_items, item_data_position=selected_position)
    # Update your GUI with the new items data
    refresh_inventory()

# Create the "retry_selector" and add it to the layout
retry_selector = QComboBox()
retry_selector.setEnabled(False)

# Connect the on_retry_selector_changed function to the currentIndexChanged signal
retry_selector.currentIndexChanged.connect(on_retry_selector_changed)
saveselector_layout.addWidget(retry_selector)

# Create the "save" button and add it to the saveselector_layout
save_button = QPushButton("Save")
save_button.setStyleSheet("background-color: yellow; color: black")
save_button.clicked.connect(on_save_button_clicked)
saveselector_layout.addWidget(save_button)


# add the saveselectorbox to the standardInvEdit_layout
standardInvEdit_layout.addWidget(saveselectorbox)

#select folder stuff

def update_load_save_button_color():
    global saveLoadIsPossible
    if savedropdownselector.currentIndex() != -1 and loseitemsnumber.value() > 2:
        load_save_button.setStyleSheet("background-color: green; color: white")
        saveLoadIsPossible = True
    else:
        load_save_button.setStyleSheet("background-color: yellow; color: black")
        saveLoadIsPossible = False

savedropdownselector.currentIndexChanged.connect(update_load_save_button_color)
loseitemsnumber.valueChanged.connect(update_load_save_button_color)

def update_save_button_color():
    global saveloaded
    if savedropdownselector.currentIndex() != -1 and loseitemsnumber.value() > 2 and saveloaded:
        save_button.setStyleSheet("background-color: green; color: white")
    else:
        save_button.setStyleSheet("background-color: yellow; color: black")

def on_savefolderbutton_clicked():
    global folder_path
    # Replace this comment with the code from the second box
    qt_path = QFileDialog.getExistingDirectory(None, "Select Save Folder")
    folder_path = QDir.toNativeSeparators(qt_path)
    refresh_save_files()

savefolderbutton.clicked.connect(on_savefolderbutton_clicked)


# add item_editor_group_box with 90% stretch to standardInvEdit_layout
standardInvEdit_layout.addWidget(item_editor_group_box, 9)

#add create_money_box with 10% stretch to standardInvEdit_layout
standardInvEdit_layout.addWidget(create_money_box(), 1)


#add the taps to the main layout
tab_widget.addTab(tab1, "Standard Inventory Editor")
tab_widget.addTab(tab2, "Empty Tab")
main_layout.addWidget(tab_widget)




central_widget.setLayout(main_layout)

main_window.show()

exit_code = app.exec()

if gof2_installation:
    gof2_installation.close()

sys.exit(exit_code)
