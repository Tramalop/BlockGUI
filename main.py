import os
import sys

import json

from PyQt5.QtCore import QLineF, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene, QGraphicsView, QToolBar, QAction, QStatusBar, QInputDialog
from PyQt5.QtGui import QBrush, QColor, QPen

import functions

# Creating a subclass of line QGraphicsLineItem that will show a dynamic link between linked Blocks
class Link(QGraphicsLineItem):
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.setPen(QPen(Qt.blue, 2))
        self.update_position()

    def update_position(self):
        p1 = self.start_item.sceneBoundingRect().center()
        p2 = self.end_item.sceneBoundingRect().center()
        self.setLine(QLineF(p1, p2))
        self.setPen(QPen(Qt.blue, 2))
        
# Creating a subclass of circle QGraphicsEllispeItem that will serve as linking nodes
class Node(QGraphicsEllipseItem):
    selected_nodes = [] # Class-level attribute to link nodes two by two

    def __init__(self, x=0, y=0, radius=5, parent=None):
        super().__init__(-radius, -radius, 2*radius, 2*radius, parent)
        self.setBrush(QBrush(QColor("lightGray")))
        self.setPos(x, y)

        # List of the links linked to this node
        self.selected_links = []

        # Enables the node to be selected and detected when moved
        self.setFlags(QGraphicsEllipseItem.ItemIsSelectable | QGraphicsItem.ItemSendsScenePositionChanges)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
           Node.selected_nodes.append(self)
           if len(Node.selected_nodes) == 2 :    
            if Node.selected_nodes[0].scenePos() != Node.selected_nodes[1].scenePos():
                # make a protection against link duplicates
                self.linkNodes(Node.selected_nodes[0], Node.selected_nodes[1])
                
            Node.selected_nodes.clear()
        else:
            super().mousePressEvent(event)

    def linkNodes(self, node1, node2):
        scene = node1.scene()
        link = Link(node1, node2)
        node1.selected_links.append(link)
        node2.selected_links.append(link)
        scene.addItem(link)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            print(f"Scene position changed to: {self.scenePos()}")
            for l in self.selected_links:
                print(type(l))
                l.update_position()
        return super().itemChange(change, value)
            

# Creating a subclass of rectangle QGraphicsRectItem to put in the canva QGraphicsScene
class Block(QGraphicsRectItem):
    internal_counter = 0 # Class-level attribute to track instances

    def __init__(self, x, y, width=100, height=50, node_radius = 5):
        super().__init__(0, 0, width, height)
        self.index = Block.internal_counter # Assign current index
        Block.internal_counter += 1 # Increment for next block
        self.setBrush(QBrush(QColor("lightGray")))
        self.setPos(x,y) # Keeps items local origin to (0, 0) when initiated which simplifies transformations, alignment, and drawing.
        
        # Creating linking nodes
        self.node_radius = node_radius
        self.node_list = []
        self.add_node("left", 0, height / 2)
        self.add_node("right", width, height / 2)

        # Enables the block to be dragged and dropped 
        self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable)

    def add_node(self, name, center_x, center_y):
        r = self.node_radius
        node = Node(center_x, center_y, r, self)
        node.setToolTip(f"{name} node") # Displays the node name when the mouse hovers over it
        node.setZValue(1)  # Makes sure it's drawn above the block
        self.node_list.append(node)

    def Change(self, change, value):
            if change == QGraphicsItem.ItemScenePositionHasChanged:
                print(f"Chnagee cene position changed to: {self.scenePos()}")
            return super().Change(change, value)

        # Enables them to be linked with a QGraphicsLineItem
    #def mousePressEvent :
    #    if event.button() == Qt.RightButton:
    #    else
    #       super.mousePressEvent()
# Creating a subclass of QMainWindow to customize it
class MainWindow(QMainWindow):
    def __init__(self, width, height):
        super().__init__()
        
        # Creating a JSON file
        self.currentFile = functions.create_unique_json()
        
        # Definition of the MainWindow
        self.setWindowTitle("BlockGUI")
        self.resize(height,width)
        self.showMaximized()

        # Create the canva
        self.scene = QGraphicsScene()

        # self.scene.addItem(Block(100, 100))
        # self.scene.addItem(Block(250, 150))

        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        self.scene.setBackgroundBrush(QBrush(QColor("white")))

        # self.scene.addItem(Block(100, 100))

        # Add a StatusBar that contains menu help for the toolbar
        self.setStatusBar(QStatusBar(self))

        # Definition of the toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # New file action
        new_action = QAction("New", self)
        new_action.setStatusTip("Create a new file")
        new_action.triggered.connect(self.create_unique_json_method)
        toolbar.addAction(new_action)

        # Rename file action
        rename_action = QAction("Rename", self)
        rename_action.setStatusTip("Rename the current file")
        rename_action.triggered.connect(self.rename_json_file_method)
        toolbar.addAction(rename_action)

        # Save blocks configuration
        save_action = QAction("Save", self)
        save_action.setStatusTip("Save the current block configuration") 
        save_action.triggered.connect(self.save_config_json_method)
        toolbar.addAction(save_action)

        # Create a block action
        block_action = QAction("Block", self)
        block_action.setStatusTip("Create a block")
        block_action.triggered.connect(self.create_block_method)
        toolbar.addAction(block_action)

        # Disable the toggle view action (removes it from the right-click menu)
        toolbar.toggleViewAction().setEnabled(False)

        # Make the toolbar immovable too
        toolbar.setMovable(False)

    def create_unique_json_method(self, base_name="Unnamed"):
        name_counter = 0
        while True:
            # Construct file name: "Unnamed.json", "Unnamed1.json", "Unnamed2.json", etc.
            file_name = f"{base_name if name_counter == 0 else f'{base_name}{name_counter}'}.json"

            # Check if the file exists
            if not os.path.exists(file_name):
                # File doesn't exist, so create it with empty JSON object
                with open(file_name, 'w') as f:
                    json.dump({}, f, indent=4)
                    self.statusBar().showMessage(f"Created new file: {file_name}")
                    self.currentFile = file_name
                return True

            # Increment counter and try next name
            name_counter += 1
    
    def rename_json_file_method(self):
        # Show an input dialog and get the text
        new_name, ok = QInputDialog.getText(self, "Renaming current file", "Enter the new file name:")
        old_name = self.currentFile
        if ok and new_name:
            # Ensure both names end with .json
            if not old_name.endswith('.json'):
                old_name += '.json'
            if not new_name.endswith('.json'):
                new_name += '.json'

        # Check if the original file exists
        if not os.path.exists(old_name):
            self.statusBar().showMessage(f"File '{old_name}' does not exist.")
            return False

        # Check if the new file name already exists to avoid overwriting
        if os.path.exists(new_name):
            self.statusBar().showMessage(f"A file named '{new_name}' already exists. Aborting rename.")
            return False

        # Perform the rename
        os.rename(old_name, new_name)
        self.currentFile = new_name
        self.statusBar().showMessage(f"Renamed '{old_name}' to '{new_name}'.")
        return True

    def save_config_json_method(self):
        item_list = self.scene.items()
        for i, item in enumerate(item_list):
            print(f"  Item {i+1}: {type(item).__name__}, at position {item.pos()}")

            # data = {
            #     i: item for i
            #     , {type(item).__name__}
            # }
    
    def create_block_method(self):
        self.scene.addItem(Block(10,10))
        self.statusBar().showMessage("Creating a block")
        # find a way to make a fixed scene and put the block in the top left

    # def write_to_json_method(self, element_name="Block")
    #     data = {
    #         "element", element_name
    #         ""
    #     } with open(filename, 'w') as f:
    #    json.dump(data, f, indent=4)

# Create a PyQt app
app = QApplication(sys.argv)

# Get the primary screen
screen = app.primaryScreen()

# Get the screen size
size = screen.size()
height = size.height()
width = size.width()

# Create the instance of the MainWindow
window = MainWindow(height//2, width//2)
window.show()
# Start the app
sys.exit(app.exec())
