from plyfile import PlyData, PlyElement
import numpy as np

def filter_sh_level(input_ply, output_ply, target_level):
    rest_counts = {0: 0, 1: 9, 2: 24, 3: 45}
    keep_count = rest_counts.get(target_level, 45)
    
    plydata = PlyData.read(input_ply)
    vertex_data = plydata['vertex'].data
    
    properties_to_keep = []
    for prop in vertex_data.dtype.names:
        if prop.startswith('f_rest_'):
            idx = int(prop.split('_')[-1])
            if idx < keep_count:
                properties_to_keep.append(prop)
        else:
            properties_to_keep.append(prop)
            
    new_dtype = np.dtype([(name, vertex_data.dtype[name]) for name in properties_to_keep])
    new_data = np.empty(len(vertex_data), dtype=new_dtype)
    for name in properties_to_keep:
        new_data[name] = vertex_data[name]
        
    new_vertex_element = PlyElement.describe(new_data, 'vertex')
    PlyData([new_vertex_element]).write(output_ply)