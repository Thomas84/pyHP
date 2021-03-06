__title__ = "Min area"
__doc__ = "Fill in minimal area requirement based on a formatted excel file"

from pyrevit import revit, DB, forms
import xlrd
from rpw.ui.forms import (FlexForm, Label, ComboBox, Separator, Button)

def convert_to_internal(from_units):
    # convert project units to internal
    d_units = DB.Document.GetUnits(revit.doc).GetFormatOptions(DB.UnitType.UT_Area).DisplayUnits
    converted = DB.UnitUtils.ConvertToInternalUnits(from_units, d_units)
    return converted


# pick excel file and read
path = forms.pick_file(file_ext='xlsx')
book = xlrd.open_workbook(path)
worksheet = book.sheet_by_index(0)

# create dictionary with min requirements, of format [unit type][room name] : min area
area_dict = {}
for i in range(1, worksheet.ncols):
    area_dict[worksheet.cell_value(0, i)] = {}
    for j in range(1, worksheet.nrows):
        area_dict[worksheet.cell_value(0, i)][worksheet.cell_value(j, 0)] = worksheet.cell_value(j, i)

coll_rooms = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Rooms).ToElements()

# take only placed rooms
good_rooms = [r for r in coll_rooms if r.Area != 0]

# a list of variations for Living / Dining / Kitchen room name
lkd_var = ["LKD",
           "LDK",
           "KLD",
           "KDL",
           "DKL",
           "DLK",
           "Living",
           "Kitchen",
           "Dining",
           "L/K/D",
           "L/D/K",
           "K/L/D",
           "K/D/L",
           "D/K/L",
           "D/L/K",
           "L-K-D",
           "L-D-K",
           "K-L-D",
           "K-D-L",
           "D-K-L",
           "D-L-K",
           ]

element_parameter_set = good_rooms[0].Parameters


room_params = [p.Definition.Name for p in element_parameter_set if
               p.StorageType.ToString() == "Double" and p.IsReadOnly == False]

room_params.sort()

components = [Label("Select room parameter to populate"), ComboBox("room_tx_params", room_params, default="Area Requirement"), Button ("Select")]
form = FlexForm("Select Parameter", components)
form.show()
selected_parameter = form.values["room_tx_params"]

if selected_parameter:
    with revit.Transaction("Write Parameter", revit.doc):
        for room in good_rooms:
            # get room parameters
            area_req = room.LookupParameter(selected_parameter)
            unit_type = room.LookupParameter("Unit Type").AsString()
            room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
            # check if Living/Kitchen/Dining is written differently
            if room_name.split()[0] in lkd_var or room_name.split("/")[0] in lkd_var:
                room_name = "Living / Dining / Kitchen"
            # look for room in dictionary and set Area Requirement value
            try:
                get_req = area_dict[unit_type][room_name]
                area_req.Set(convert_to_internal(get_req))
            except:
                area_req.Set(0)



