import struct
import os
#for now the input and output file have a hardcoded name but this will change
file_in = "gof2_save_game_4"
marker = b"\xFF\xFF\xFF\xFF\x38"
file_out = file_in + "_edited"

def read_item_data(file_in, marker):
    #file_out = file_in + "_edited"
    items = []
    quantity_of_items = ''
    with open(file_in, "rb") as file_save:

        marker_size = len(marker)
        file_bytes = file_save.read()
        index = file_bytes.find(marker)
        if index < 0:
            raise ValueError("Could not find marker in file")
        file_save.seek(index + marker_size + 26)
        quantity_of_items = struct.unpack("I", file_save.read(4))[0]
        print('number of items: '+str(quantity_of_items))
        for i in range(quantity_of_items):
            item_ID = struct.unpack("I", file_save.read(4))[0]
            quantity_of_this_item = struct.unpack("I", file_save.read(4))[0]
            item_price = struct.unpack("I", file_save.read(4))[0]
            file_save.seek(1 ,1)
            items.append((item_ID, quantity_of_this_item, item_price))
    return items

def save_item_data(file_in, marker, items):
    items_old =items




    #items is wahts going to be in your inventory
    #(itemid, how mutch of this item, how expensive it is (its not important))

    items = [(0, 999, 4), (1, 999, 4), (2, 999, 4), (3, 999, 4), (4, 999, 4), (5, 999, 4), (6, 999, 4)]
    
    #if you just want all items then just remove the # in the next row
    #items = [(i, 999, 4) for i in range(196)]





    quantity_of_items = len(items)
    file_out = file_in + "_edited"

    with open(file_in, "rb") as f:
        file_bytes = f.read()

        marker_size = len(marker)

        start_of_item_data = file_bytes.find(marker) + marker_size + 26
        end_of_item_data = start_of_item_data + (13 * len(items_old)) +4
        end_of_file = len(file_bytes)

        # Copy the data before the item data to the new file
        with open(file_out, "wb") as f2:
            f2.write(file_bytes[:start_of_item_data])

            #Add number of items
            f2.write(struct.pack("I", quantity_of_items))
            
            total_item_data_length = sum(len(struct.pack("III", *item) + b"\x00") for item in items)
            
            # Write the updated item data from the list
            for item in items:
                f2.write(struct.pack("III", *item)+ b"\x00")

            # Copy the data after the item data to the new file
            f2.write(file_bytes[end_of_item_data:end_of_file])


items = read_item_data(file_in=file_in, marker=marker)
save_item_data(file_in=file_in, marker=marker, items=list(items))
items_edited = read_item_data(file_out, marker)
print(items)
print(items_edited)







