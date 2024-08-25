# Use in QGIS Python console to apply a selected buffer distance  to polygons in a selected layer

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsWkbTypes, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle
from qgis.utils import iface

class BufferDialog(QDialog):
    def __init__(self, parent=None):
        super(BufferDialog, self).__init__(parent)
        self.setWindowTitle("Buffer Polygons by Distance")

        self.layout = QVBoxLayout(self)

        # Layer Name Input
        self.layer_name_label = QLabel("Layer Name:")
        self.layout.addWidget(self.layer_name_label)
        self.layer_name_input = QLineEdit(self)
        self.layout.addWidget(self.layer_name_input)

        # Projection CRS Input
        self.crs_label = QLabel("Target CRS (e.g., EPSG:3857):")
        self.layout.addWidget(self.crs_label)
        self.crs_input = QLineEdit(self)
        self.layout.addWidget(self.crs_input)

        # Buffer Distance Input
        self.label = QLabel("Buffer Distance (meters):")
        self.layout.addWidget(self.label)
        self.distance_input = QLineEdit(self)
        self.layout.addWidget(self.distance_input)

        # Buffer Button
        self.buffer_button = QPushButton("Buffer Polygons", self)
        self.buffer_button.clicked.connect(self.buffer_polygons)
        self.layout.addWidget(self.buffer_button)

    def buffer_polygons(self):
        layer_name = self.layer_name_input.text()
        target_crs_str = self.crs_input.text()
        distance_str = self.distance_input.text()

        # Validate inputs
        try:
            distance = float(distance_str)
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter a valid number for buffer distance.")
            return

        # Find the layer by name
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if not layers:
            QMessageBox.critical(self, "Layer Error", "Layer not found.")
            return
        layer = layers[0]

        # Check if the layer is a polygon layer
        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            QMessageBox.critical(self, "Layer Error", "The selected layer must be a polygon layer.")
            return

        # Transform the layer CRS to the target CRS
        target_crs = QgsCoordinateReferenceSystem(target_crs_str)
        if not target_crs.isValid():
            QMessageBox.critical(self, "CRS Error", "Invalid target CRS.")
            return

        # Get the current layer CRS
        source_crs = layer.crs()

        # Create a coordinate transform
        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance().transformContext())

        # Perform buffering
        buffered_layer = self.buffer_layer(layer, distance, transform, target_crs)

        # Add the result to the QGIS canvas
        QgsProject.instance().addMapLayer(buffered_layer)

        QMessageBox.information(self, "Success", "Buffer applied and layer added to the map.")

    def buffer_layer(self, layer, distance, transform, target_crs):
        # Create a new memory layer for the buffered polygons
        buffered_layer = QgsVectorLayer(f"Polygon?crs={target_crs.authid()}", "Buffered Layer", "memory")
        provider = buffered_layer.dataProvider()
        provider.addAttributes(layer.dataProvider().fields())
        buffered_layer.updateFields()

        features = []
        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom:
                # Transform geometry to the target CRS
                geom.transform(transform)
                # Apply the buffer
                buffered_geom = geom.buffer(distance, 5)
                # Create a new feature with the buffered geometry
                new_feature = QgsFeature()
                new_feature.setGeometry(buffered_geom)
                new_feature.setAttributes(feature.attributes())
                features.append(new_feature)

        provider.addFeatures(features)
        buffered_layer.updateExtents()

        return buffered_layer
        
dlg = BufferDialog()
dlg.exec_()
        
        