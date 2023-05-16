# Gof2-Inventory-Editor
A work in progress python skript / tool wher you can edit your item inventory


here is the first puplic gui version :D


![image](https://github.com/Manni1000/Gof2-Inventory-Editor/assets/62727737/22d938ce-409b-44ee-8d20-539fdca8eedc)

soon i will make the code cleaner so addin new stuff gets easyer x.x

also this is for the pc version but if you chage some stuff in the code (mainly the possision where the money value is stored) then it also works for mobile
always make backups of your saves this tool might destroy your saves

it may work on widows.
if you want to have the item icons you have to create a folder caled images in it you shuld add every image from every item with the right names.







item structure:
![2023-02-23_05-16](https://user-images.githubusercontent.com/62727737/220820638-0e4d7bfe-f25a-426c-94fc-b5ac86af38ca.png)

also all the data is stored in little endian

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
