# Gof2-Inventory-Editor
A work in progress python skript wher you can edit your item inventory


i will also add a cli and maby a gui but for now you have to open the script and change the nubers of the items variable

for now the imput file has to be named gof2_save_game_4
the preview save file with the same number has to exist but the data in it does not matter

also this is for the pc version i might also make it work for mobile

item structure:
![2023-02-23_05-16](https://user-images.githubusercontent.com/62727737/220820638-0e4d7bfe-f25a-426c-94fc-b5ac86af38ca.png)

also all the data is stored in little endian

(i am not sure about the marker)
marker = 5 bytes
spacer = 26 bytes

item_count = 4 bytes
item_ID = 4 bytes
item_count = 4 bytes
item_cost =4 bytes
spacer = 1 byte

item_count = 4 bytes
item_ID = 4 bytes
item_count = 4 bytes
item_cost =4 bytes
spacer = 1 byte

item_count = 4 bytes
item_ID = 4 bytes
item_count = 4 bytes
item_cost =4 bytes
spacer = 1 byte

.....
....
...
