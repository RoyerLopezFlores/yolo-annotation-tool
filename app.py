import cv2
import os
import numpy as np
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout,QListWidget
from PyQt6.QtGui import QPixmap, QImage,QPainter,QPen,QColor,QKeyEvent
from PyQt6.QtCore import Qt,QRect
import sys
PATH_BASE = "E:/yolo_data/hasty_post/hasty_post4"
PATH_IMAGES = os.path.join(PATH_BASE, "images")
PATH_LABELS = os.path.join(PATH_BASE, "labels")
class_names = ["post", "react_fb"]
hasty = False
colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255), QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)]
def resize_image_to_height(img, max_height=800):
    h, w = img.shape[:2]
    if h <= max_height:
        return img
    scale = max_height / h
    new_w = int(w * scale)
    resized_img = cv2.resize(img, (new_w, max_height), interpolation=cv2.INTER_AREA)
    return resized_img
def load_yolo_labels(label_path, img_width, img_height):
    boxes = []
    with open(label_path, 'r') as file:
        for line in file:
            data_line = list(map(float, line.strip().split()))
            if hasty:
                class_id = data_line[0]
                for index in range(len(data_line[1:]) // 4):
                    x_center, y_center, width, height = data_line[1 + index * 4: 5 + index * 4]
                    # Convertir a píxeles y a coordenadas de esquina (xmin, ymin, xmax, ymax)
                    x_center *= img_width
                    y_center *= img_height
                    width *= img_width
                    height *= img_height

                    xmin = int(x_center - width / 2)
                    ymin = int(y_center - height / 2)
                    xmax = int(x_center + width / 2)
                    ymax = int(y_center + height / 2)

                    boxes.append((int(class_id), xmin, ymin, xmax, ymax))
            else:
                #Yolo fomato
                class_id = int(data_line[0])
                x_center, y_center, width, height = data_line[1:5]
                # Convertir a píxeles y a coordenadas de esquina (xmin, ymin, xmax, ymax)
                x_center *= img_width
                y_center *= img_height
                width *= img_width
                height *= img_height
                xmin = int(x_center - width / 2)
                ymin = int(y_center - height / 2)
                xmax = int(x_center + width / 2)
                ymax = int(y_center + height / 2)
                boxes.append((class_id, xmin, ymin, xmax, ymax))
    return boxes

def draw_boxes(img, boxes, class_names=None):
    for class_id, xmin, ymin, xmax, ymax in boxes:
        color = (0, 255, 0)
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color, 2)
        label = class_names[class_id] if class_names and class_id < len(class_names) else str(class_id)
        cv2.putText(img, label, (xmin, max(0, ymin - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img
def convert_cv_to_qpixmap(cv_img):
    
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(q_image)
class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.cls_boxes = []  # Lista de cajas manuales por clase
        self.index_class = 0
        self.cls_default = []  # Lista de cajas por defecto
    def setIndexClass(self, index_class):
        self.index_class = index_class
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.position().toPoint()
            rect = QRect(self.start_point, self.end_point).normalized()
            
            self.cls_boxes.append((self.index_class, rect))
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap():
            painter = QPainter(self)
            painter.setPen(QPen(colors[self.index_class], 2))

            # Dibujar rectángulo activo
            if self.drawing and self.start_point and self.end_point:
                rect = QRect(self.start_point, self.end_point).normalized()
                painter.drawRect(rect)

            # Dibujar todos los rectángulos guardados
            for box in self.cls_boxes:
                painter.setPen(QPen(colors[box[0]], 2))
                painter.drawRect(box[1])
    def clean(self):
        self.boxes = []
        self.cls_boxes = []
        self.update()
    def saveBoxesFormattedYolo(self, filename,dimensions):
        if len(self.cls_boxes)==0:
            return
        operation_file = 'w'
        if os.path.exists(filename):
            operation_file = 'a'

        with open(filename, operation_file) as file:

            for box in self.cls_boxes:
                class_id, rect = box
                padd_x = (self.width() - dimensions[0])*0.5
                x1 = max(rect.left(),padd_x)
                x2 = min(rect.right(), padd_x + dimensions[0])
                x_center = (x1 + x2) / 2 - padd_x
                y_center = (rect.top() + rect.bottom()) / 2
                width = x2 - x1
                height = rect.height()
                # Normalizar coordenadas
                print(self.width(),self.height())

                x_center /= dimensions[0]
                y_center /= dimensions[1]
                width /= dimensions[0]
                height /= dimensions[1]
                x_center = min(max(x_center, 0), 1)
                y_center = min(max(y_center, 0), 1)
                width = min(max(width, 0), 1)
                height = min(max(height, 0), 1)
                file.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
class YoloViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO Viewer")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.image_files = [
            f for f in os.listdir(PATH_IMAGES)
            if f.lower().endswith(('.jpg', '.png'))
        ]
        self.index = 0
        self.index_class = 0
        self.image_dimension = None
        # Lista de archivos a la izquierda
        self.list_widget = QListWidget()
        self.list_widget.addItems(class_names)
        self.list_widget.setMaximumWidth(200)
        self.list_widget.itemClicked.connect(self.on_item_clicked)

        # Imagen al centro
        self.image_label = ImageLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Botones abajo
        self.prev_button = QPushButton("Anterior")
        self.next_button = QPushButton("Siguiente")
        self.clean_button = QPushButton("Clear")
        self.prev_button.clicked.connect(self.show_prev)
        self.next_button.clicked.connect(self.show_next)
        
        self.clean_button.clicked.connect(self.clearBoxes)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.prev_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addWidget(self.clean_button)

        # Parte derecha (imagen + botones)
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.image_label)
        right_layout.addLayout(buttons_layout)

        # Layout principal horizontal
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

        self.show_image()
    def on_item_clicked(self, item):
        filename = item.text()
        self.index_class = class_names.index(filename)
        self.image_label.setIndexClass(self.index_class)

    def show_image(self):
        if not self.image_files:
            self.image_label.setText("No hay imágenes en la carpeta.")
            return

        image_file = self.image_files[self.index]
        image_path = os.path.join(PATH_IMAGES, image_file)
        label_path = os.path.join(PATH_LABELS, os.path.splitext(image_file)[0] + ".txt")

        img = cv2.imread(image_path)
        img = resize_image_to_height(img, max_height=800)

        h, w = img.shape[:2]
        self.image_dimension = (w, h)
        if os.path.exists(label_path):
            boxes = load_yolo_labels(label_path, w, h)
            #if len(boxes)>0:
            #    self.image_label.cls_default = [(box[0], QRect(box[1], box[2], box[3], box[4])) for box in boxes]
        else:
            boxes = []
        self.image_label.clean()  # limpiar cajas manuales

        img = draw_boxes(img, boxes, class_names)
        pixmap = convert_cv_to_qpixmap(img)
        self.image_label.setPixmap(pixmap)
    def save_boxes(self):
        if not self.image_files:
            return

        image_file = self.image_files[self.index]
        label_path = os.path.join(PATH_LABELS, os.path.splitext(image_file)[0] + ".txt")
        self.image_label.saveBoxesFormattedYolo(label_path,self.image_dimension)
        #print(f"Saved boxes to {label_path}")
    def clearBoxes(self):
        if not self.image_files:
            return

        image_file = self.image_files[self.index]
        label_path = os.path.join(PATH_LABELS, os.path.splitext(image_file)[0] + ".txt")
        if os.path.exists(label_path):
            os.remove(label_path)
            print(f"Removed boxes from {label_path}")
            self.image_label.clean()
            self.image_label.update()
            self.show_image()
        else:
            print(f"No label file found to remove: {label_path}")

    def show_next(self):
        self.save_boxes()
        self.index = (self.index + 1) % len(self.image_files)
        self.show_image()

    def show_prev(self):
        self.save_boxes()
        self.index = (self.index - 1) % len(self.image_files)
        self.show_image()
    def keyPressEvent(self, event:QKeyEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_X:
                if len(self.image_label.cls_boxes)>0:
                    self.image_label.cls_boxes.pop()
                    self.image_label.update()
            if event.key() == Qt.Key.Key_Space:
                self.show_next()
            
        #if event.modifiers & Qt.KeyboardModifier.ShiftModifier:
        #    if event.key() == Qt.Key.Key_S:
        #        self.save_boxes()
        return super().keyPressEvent(event)
# Cambia esto por tu ruta
#files_images = os.listdir(PATH_IMAGES)
#files_labels = os.listdir(PATH_LABELS)
#image_path = os.path.join(PATH_IMAGES, files_images[2])  # Cambia el índice para otra imagen
#
#label_path = os.path.splitext(image_path)[0] + '.txt'  # mismo nombre, extensión .txt
#background = False
#if label_path not in files_labels:
#    print(f"Label file {label_path} not found.")
#    background = True
## Leer imagen
#img = cv2.imread(image_path)
#h, w = img.shape[:2]
#
## Cargar etiquetas
#if not background:
#    boxes = load_yolo_labels(label_path, w, h)
#else:
#    boxes = []
## (Opcional) Nombres de clases
#class_names = ["1","2"]  # cambia esto según tu dataset
#
## Dibujar cajas
#draw_boxes(img, boxes, class_names)
#
## Mostrar imagen
#cv2.imshow("YOLO Labels", img)
#cv2.waitKey(0)
#cv2.destroyAllWindows()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = YoloViewer()
    viewer.resize(800, 600)
    screen = app.primaryScreen()
    screen_geometry = screen.availableGeometry()

    # Centrar horizontalmente y alinear arriba
    screen_width = screen_geometry.width()
    x = (screen_width - viewer.width()) // 2
    y = 0  # Arriba de la pantalla
    viewer.move(x, y)

    viewer.show()
    sys.exit(app.exec())