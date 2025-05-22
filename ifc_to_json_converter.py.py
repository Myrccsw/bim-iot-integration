import ifcopenshell
import ifcopenshell.util
import ifcopenshell.util.element
import json
import os
from ifcopenshell import geom

# Define output directory
output_directory = r"C:\Users\xxx"

# Ensure the directory exists
os.makedirs(output_directory, exist_ok=True)

# Define the output file path
output_file_path = os.path.join(output_directory, "json_listData.json")

# Load your IFC file
ifc_file = ifcopenshell.open(r"C:\Users\xxx.ifc")

### JSON DATA IN LIST ###
settings = geom.settings(
    STRICT_TOLERANCE=True,
    USE_WORLD_COORDS=True
)

products = ifc_file.by_type("IfcProduct")

verts = []
faces = []
data = []
json_listData = {}

# Helper function to get IfcDocumentReference
def get_document_reference(ifc_element):
    """Find related IfcDocumentReference objects."""
    document_references = []
    for rel in ifc_file.by_type("IfcRelAssociatesDocument"):
        if ifc_element in rel.RelatedObjects:
            for doc in rel.RelatingDocument:
                if doc.is_a("IfcDocumentReference") and hasattr(doc, "Reference"):
                    document_references.append(doc.Reference)
    return document_references

# Helper function to collect quantity data (from IfcElementQuantity)
def get_quantity_data(ifc_element):
    """
    Parse any IfcElementQuantity sets attached to this element,
    storing each quantity's Name -> numeric value in a dictionary.
    """
    quantity_data = {}
    # If the element has relationships defining property sets
    if hasattr(ifc_element, "IsDefinedBy"):
        for rel_def in ifc_element.IsDefinedBy:
            # We only want IfcRelDefinesByProperties
            if rel_def.is_a("IfcRelDefinesByProperties"):
                prop_def = rel_def.RelatingPropertyDefinition
                # Check if it's an IfcElementQuantity
                if prop_def.is_a("IfcElementQuantity"):
                    # prop_def.Name might be something like "BaseQuantities", etc.
                    # Each quantity is an IfcPhysicalSimpleQuantity (IfcQuantityLength, etc.)
                    for q in prop_def.Quantities:
                        if q.is_a("IfcQuantityLength"):
                            quantity_data[q.Name] = float(q.LengthValue)
                        elif q.is_a("IfcQuantityArea"):
                            quantity_data[q.Name] = float(q.AreaValue)
                        elif q.is_a("IfcQuantityVolume"):
                            quantity_data[q.Name] = float(q.VolumeValue)
                        elif q.is_a("IfcQuantityCount"):
                            quantity_data[q.Name] = float(q.CountValue)
                        elif q.is_a("IfcQuantityWeight"):
                            quantity_data[q.Name] = float(q.WeightValue)
                        # You can handle other IfcQuantityXXX types similarly if needed
    return quantity_data

# Iterate over each product instance
for product in products:
    if product.Representation:
        tempDat = {}

        # Basic IFC Info from get_info()
        for key in list(product.get_info().keys()):
            use_key = key[0].lower() + key[1:]
            if key not in ["OwnerHistory", "ObjectPlacement", "Representation"]:
                val = product.get_info()[key]
                if val:
                    tempDat.update({use_key: val})

        # Document Reference
        
        doc_refs = get_document_reference(product)
        if doc_refs:
            tempDat["documentReferences"] = doc_refs

        # Collect quantity data
        quantity_data = get_quantity_data(product)
        if quantity_data:
            tempDat["quantityData"] = quantity_data

        # Store this product info
        data.append(tempDat)

        # Create geometry (vertices, faces)

        shape = geom.create_shape(settings, product)
        flattened_vertices = shape.geometry.verts
        vertices = [flattened_vertices[i : i + 3] for i in range(0, len(flattened_vertices), 3)]
        verts.append(vertices)  
        faces.append(shape.geometry.faces)  
        
        
        # indexes, each triple forms one triangle

# Now attach the geometry points to each product’s data
for idx in range(len(faces)):
    points = []
    for face_index in faces[idx]:
        points.append(verts[idx][face_index])
    data[idx].update({"points": points})

json_listData.update({"data": data})

# Export to JSON File
json_string = json.dumps(json_listData, indent=4)

with open(output_file_path, "w", encoding="utf-8") as output_file:
    output_file.write(json_string)

print(f"JSON data with quantity sets has been exported to {output_file_path}")

