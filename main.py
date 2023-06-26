from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QApplication,
    QFileDialog,
    QStyle,
    QColorDialog,
    QTabWidget,
    QTableWidget,
    QGridLayout,
    QComboBox,
    QScrollArea,
    QStackedWidget,
    QLabel,
)
from PySide6.QtCore import (
        Qt,
        Slot,
        QStandardPaths,
        QRect,
        QRectF,
        Signal,
)
from PySide6.QtGui import (
    QMouseEvent,
    QPaintEvent,
    QPen,
    QAction,
    QPainter,
    QColor,
    QPixmap,
    QIcon,
    QKeySequence,
)
import sys

from PIL.ImageQt import ImageQt

class AnnotatorWidget(QWidget):

    def __init__(self, pages, label_table, parent=None):
        super().__init__(parent)

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.parent_label_table = label_table

        self.painter_widget_holder = QStackedWidget()
        [self.painter_widget_holder.addWidget(PainterWidget(page)) for page in pages]
        self.painter_widget_holder.setCurrentIndex(0)
        self.grid.addWidget(self.painter_widget_holder, 0, 0, 20, 3)

        self.label_table_holder = QStackedWidget()
        [self.label_table_holder.addWidget(QTableWidget(0, 2)) for _ in pages]
        [self.label_table_holder.widget(i).setHorizontalHeaderLabels(['value', 'label']) for i in range(self.label_table_holder.count())]
        #[self.label_table_holder.widget(i).insertRow(0) for i in range(self.label_table_holder.count())]
        #[self.label_table_holder.widget(i).insertColumn(0) for i in range(self.label_table_holder.count())]
        self.label_table_holder.setCurrentIndex(0)
        self.grid.addWidget(self.label_table_holder, 2, 4)

        [self.painter_widget_holder.widget(i).clicked.connect(self.on_new_rectangle) for i in range(self.painter_widget_holder.count())]

        self.page_label = QLabel('Page')
        self.page_selector = QComboBox()
        self.page_selector.currentIndexChanged.connect(self.on_page_change)
        self.page_selector.addItems([f'{i}' for i in range(self.painter_widget_holder.count())])
        self.grid.addWidget(self.page_label, 0, 4)
        self.grid.addWidget(self.page_selector, 1, 4)



    @Slot()
    def on_page_change(self):
        self.painter_widget_holder.setCurrentIndex(self.page_selector.currentIndex())
        self.label_table_holder.setCurrentIndex(self.page_selector.currentIndex())

    @Slot()
    def on_new_rectangle(self, event):
        new_rect = self.painter_widget_holder.currentWidget().rects[-1]

        new_row_idx = self.label_table_holder.currentWidget().rowCount()
        self.label_table_holder.currentWidget().insertRow(new_row_idx)
        label_dropdown = QComboBox()
        label_dropdown.addItems(['test1', 'test2'])
        self.label_table_holder.currentWidget().setCellWidget(new_row_idx, 1, label_dropdown)

    def clear(self):
        """ Clear the pixmap """
        self.painter_widget_holder.currentWidget().pixmap.fill(Qt.white)
        self.painter_widget_holder.currentWidget().update()

    def setColor(self, color):
        self.painter_widget_holder.currentWidget().pen.setColor(color)



class PainterWidget(QWidget):
    """A widget where user can draw with their mouse

    The user draws on a QPixmap which is itself paint from paintEvent()

    """
    clicked = Signal(Qt.MouseButton)

    def __init__(self, background=None, parent=None):
        super().__init__(parent)

        #if background is not None:
        #    self.setFixedSize(int(850*0.8), int(1100*0.8))
        #    self.pixmap = QPixmap.fromImage(qim)
        #    qim = ImageQt(im)
        #    self.pixmap.fill(Qt.white)
        #else:

        #    self.setFixedSize(int(850*0.8), int(1100*0.8))
        #    self.pixmap = QPixmap(self.size())
        #    self.pixmap.fill(Qt.white)
        self.setFixedSize(int(850*0.8), int(1100*0.8))
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(Qt.white)

        self.previous_pos = None
        self.painter = QPainter()
        self.pen = QPen()
        self.pen.setWidth(2)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)

        self.rects = []

    def paintEvent(self, event: QPaintEvent):
        """Override method from QWidget

        Paint the Pixmap into the widget

        """
        with QPainter(self) as painter:
            painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event: QMouseEvent):
        """Override from QWidget

        Called when user clicks on the mouse

        """
        self.previous_pos = event.position().toPoint()
        self.starting_pos = self.previous_pos
        QWidget.mousePressEvent(self, event)
        self.cur_rect = QRectF(self.previous_pos, self.previous_pos)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Override method from QWidget

        Called when user moves and clicks on the mouse

        """
        current_pos = event.position().toPoint()

        self.painter.begin(self.pixmap)
        self.painter.setCompositionMode(QPainter.CompositionMode_Source)
        self.painter.setRenderHints(QPainter.Antialiasing, True)
        self.painter.setPen(self.pen)
        self.painter.setBrush(Qt.white)


        erase_rect = self.cur_rect
        erase_rect.setLeft(erase_rect.x() - self.pen.width()/2)
        erase_rect.setTop(erase_rect.y() -  self.pen.width()/2)
        erase_rect.setRight(erase_rect.x() + erase_rect.width() + self.pen.width()/2)
        erase_rect.setBottom(erase_rect.y() + erase_rect.height() + self.pen.width()/2)

        self.painter.eraseRect(erase_rect)

        if current_pos.x() <= self.starting_pos.x():
            x1 = current_pos.x()
            x2 = self.starting_pos.x()
        else:
            x1 = self.starting_pos.x()
            x2 = current_pos.x()

        if current_pos.y() <= self.starting_pos.y():
            y1 = current_pos.y()
            y2 = self.starting_pos.y()
        else:
            y1 = self.starting_pos.y()
            y2 = current_pos.y()

        self.cur_rect.setCoords(x1, y1, x2, y2)
        self.painter.drawRect(self.cur_rect)

        #self.painter.drawLine(self.previous_pos, current_pos)
        self.painter.end()

        self.previous_pos = current_pos
        self.update()

        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Override method from QWidget

        Called when user releases the mouse

        """
        self.previous_pos = None
        QWidget.mouseReleaseEvent(self, event)
        self.rects.append(self.cur_rect)
        self.clicked.emit(event.button())

    def save(self, filename: str):
        """ save pixmap to filename """
        self.pixmap.save(filename)

    def load(self, filename: str):
        """ load pixmap from filename """
        self.pixmap.load(filename)
        self.pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio)
        self.update()

    def clear(self):
        """ Clear the pixmap """
        self.pixmap.fill(Qt.white)
        self.update()

class MainWindow(QMainWindow):
    """An Application example to draw using a pen """

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.tab_widget = QTabWidget()

        self.label_table = QTableWidget()

        self.annotator = AnnotatorWidget(pages=[1,2,3], label_table=self.label_table)

        self.bar = self.addToolBar("Menu")
        self.bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._save_action = self.bar.addAction(
            qApp.style().standardIcon(QStyle.SP_DialogSaveButton), "Save", self.on_save
        )
        self._save_action.setShortcut(QKeySequence.Save)
        self._open_action = self.bar.addAction(
            qApp.style().standardIcon(QStyle.SP_DialogOpenButton), "Open", self.on_open
        )
        self._open_action.setShortcut(QKeySequence.Open)
        self.bar.addAction(
            qApp.style().standardIcon(QStyle.SP_DialogResetButton),
            "Clear",
            self.annotator.clear,
        )
        self.bar.addSeparator()

        self.color_action = QAction(self)
        self.color_action.triggered.connect(self.on_color_clicked)
        self.bar.addAction(self.color_action)

        self.setCentralWidget(self.tab_widget)

        self.color = Qt.black
        self.set_color(self.color)

        self.mime_type_filters = ["image/png", "image/jpeg"]

        self.tab_widget.addTab(self.annotator, 'Annotate')
        self.tab_widget.addTab(self.label_table, 'Setup')




    @Slot()
    def on_save(self):

        dialog = QFileDialog(self, "Save File")
        dialog.setMimeTypeFilters(self.mime_type_filters)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix("png")
        dialog.setDirectory(
            QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        )

        if dialog.exec() == QFileDialog.Accepted:
            if dialog.selectedFiles():
                self.painter_widget.save(dialog.selectedFiles()[0])

    @Slot()
    def on_open(self):

        dialog = QFileDialog(self, "Save File")
        dialog.setMimeTypeFilters(self.mime_type_filters)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setDefaultSuffix("png")
        dialog.setDirectory(
            QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        )

        if dialog.exec() == QFileDialog.Accepted:
            if dialog.selectedFiles():
                self.painter_widget.load(dialog.selectedFiles()[0])

    @Slot()
    def on_color_clicked(self):

        color = QColorDialog.getColor(self.color, self)

        if color:
            self.set_color(color)

    def set_color(self, color: QColor = Qt.black):

        self.color = color
        # Create color icon
        pix_icon = QPixmap(32, 32)
        pix_icon.fill(self.color)

        self.color_action.setIcon(QIcon(pix_icon))
        self.annotator.setColor(self.color)
        self.color_action.setText(QColor(self.color).name())


if __name__ == "__main__":

    app = QApplication(sys.argv)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
