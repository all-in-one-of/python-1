import hou
import os


"""
set up vars to open file borwser to current scene save location
"""
startpath = hou.hipFile.path()
filename = hou.hipFile.name()
openpath = startpath.split(filename)[0]

"""
open file chooser to select folder to process
"""
geo_dir = hou.ui.selectFile(start_directory=openpath, title="Select Geo Directory", file_type=hou.fileType.Directory)
geo_dir_expanded = hou.expandString(geo_dir)

geo_files = os.listdir(geo_dir_expanded)


"""
initialize empty lists, prep vars for looping
"""
file_nodes = []
open_nodes = []
importer = hou.node('/obj').createNode('geo', 'imported_geo')
i = 0
prevBound = 0

"""
Main Loop. For each file in selected dir, set up given node network with specified parameters
"""

for geo in geo_files:
    geo_name = os.path.splitext(geo)[0]                         #load geo, set error handling
    geo_file_node = importer.createNode('file', geo_name)
    geo_path = geo_dir_expanded + geo
    geo_file_node.parm("file").set(geo_path)
    geo_file_node.parm("missingframe").set(1)
    connected = geo_file_node.createOutputNode('connectivity')  #add connectivity node, color per piece
    colored = connected.createOutputNode('color')
    colored.parm('colortype').set(4)
    colored.parm('rampattribute').set('class')
    geo_unit = colored.createOutputNode('sop_axis_align')       #axis align, make unit size
    geo_unit.parm('bUnitSize').set(1)
    geo_xform_node = geo_unit.createOutputNode('xform')
    group = geo_xform_node.createOutputNode('groupcreate')      #create group of any unshared edges
    group.parm('grouptype').set(2)
    group.parm('groupbase').set(0)
    group.parm('groupedges').set(1)
    group.parm('unshared').set(1)
    Edges = hou.SopNode.geometry(group)
    edgesGroup = Edges.edgeGroups()[0]
    numEdges = len(edgesGroup.edges())
    if numEdges > 0:                                            #if grop members > 0, set warnings
        open_nodes.append(group)
        group.setColor(hou.Color(1.0, 0.0, 0.0))
        group.appendComment('WARNING: open edges found')
        group.setGenericFlag(hou.nodeFlag.DisplayComment, 1)
        
        
    """
    Layout grid strucutre in viewer. Current simple version as all items are unitized. 
    Some variables below are set up in anticiaption of making grid dynamic based on individual geo sizes.
    """   
    geoFetch = hou.SopNode.geometry(geo_unit)                   #Creat Bounding Box for Each Geo loaded
    boundbox = geoFetch.boundingBox()
    halfBound = (boundbox.sizevec()[0])*0.5  
    
    if i==0:                                                    #arrange all geo around origin and offset by individual bounding boxes

        geo_xform_node.parm("tx").set(0)
        prevBound += (halfBound)
    else:
        inc = 10
        col = i%inc
        row = i-col
        geo_xform_node.parm("tx").set(col)
        geo_xform_node.parm("tz").set(row / inc)
        prevBound += (boundbox.sizevec()[0])
    i += 1

    """
    make list of all geos loaded
    """
    file_nodes.append(group)

"""
merge all geo nodes, set vsibility/render flags and arange layout
"""
merge_geo = importer.createNode('merge','Merge_All')

for node in file_nodes:
    merge_geo.setNextInput(node)

importer.layoutChildren()

merge_geo.move((0,-10))
for open in open_nodes:
    open.move((0,-5))

merge_geo.move((0,-3))
merge_geo.setDisplayFlag(True)
merge_geo.setRenderFlag(True)
