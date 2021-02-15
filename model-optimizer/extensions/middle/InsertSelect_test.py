"""
 Copyright (C) 2018-2021 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
import unittest

import numpy as np

from extensions.middle.InsertSelect import AddSelectBeforeMemoryNodePattern
from mo.front.common.partial_infer.utils import int64_array
from mo.utils.ir_engine.compare_graphs import compare_graphs
from mo.utils.unittest.graph import build_graph


class InsertSelectTests(unittest.TestCase):

    # graph have no splices - selects should not be inserted
    def test_insert_select_0(self):
        graph = build_graph({
                             'placeholder_1': {'kind': 'op', 'op': 'Parameter'},
                             'placeholder_data_1': {'kind': 'data', 'shape': [1, 13]},
                             'memory': {'kind': 'op', 'op': 'Assign'},
                             },
                            [('placeholder_1', 'placeholder_data_1'),
                             ('placeholder_data_1', 'memory')
                             ],
                            nodes_with_edges_only=True)
        ref_graph = graph.copy()
        AddSelectBeforeMemoryNodePattern().find_and_replace_pattern(graph)

        (flag, resp) = compare_graphs(graph, ref_graph, 'memory')
        self.assertTrue(flag, resp)

    # graph contains 1 splice with context length 5, should be inserted select with memory as counter with length 5
    def test_insert_select_1(self):
        graph = build_graph({
                             'placeholder_1': {'kind': 'op', 'op': 'Parameter'},
                             'placeholder_data_1': {'kind': 'data', 'shape': [1, 13]},
                             'splice_1': {'kind': 'op', 'op': 'Splice', 'context': np.array([-2, -1, 0, 1, 2])},
                             'splice_data_1': {'kind': 'data', 'shape': [1, 13]},
                             'placeholder_2': {'kind': 'op', 'op': None},
                             'placeholder_data_2': {'kind': 'data', 'shape': [1, 26]},
                             'memory': {'kind': 'op', 'op': 'Assign', 'index': 0},
                             },
                            [('placeholder_1', 'placeholder_data_1'),
                             ('placeholder_data_1', 'splice_1'), ('splice_1', 'splice_data_1'),
                             ('splice_data_1', 'placeholder_2'), ('placeholder_2', 'placeholder_data_2'),
                             ('placeholder_data_2', 'memory')
                             ],
                            nodes_with_edges_only=True)
        AddSelectBeforeMemoryNodePattern().find_and_replace_pattern(graph)
        ref_graph = build_graph({
                                 'placeholder_1': {'kind': 'op', 'op': 'Parameter'},
                                 'placeholder_data_1': {'kind': 'data', 'shape': [1, 13]},
                                 'splice_1': {'kind': 'op', 'op': 'Splice', 'context': np.array([-2, -1, 0, 1, 2])},
                                 'splice_data_1': {'kind': 'data', 'shape': [1, 13]},
                                 'placeholder_2': {'kind': 'op', 'op': None},

                                 'fill_value': {'kind': 'op', 'op': 'Const', 'value': int64_array([0])},
                                 'fill_value_data': {'kind': 'data'},

                                 'shape': {'kind': 'op', 'op': 'ShapeOf'},
                                 'shape_data': {'kind': 'data'},
                                 'crop_batch': {'kind': 'op', 'op': 'Crop', 'offset': int64_array([0])},
                                 'crop_batch_data': {'kind': 'data'},
                                 'crop_batch_dim': {'kind': 'op', 'op': 'Const', 'value': int64_array([1])},
                                 'crop_batch_dim_data': {'kind': 'data'},
                                 'second_dim': {'kind': 'op', 'op': 'Const', 'value': int64_array([5])},
                                 'second_dim_data': {'kind': 'data'},
                                 'gather_shape': {'kind': 'op', 'op': 'Concat'},
                                 'gather_shape_data': {'kind': 'data'},
                                 'fill_value_ones': {'kind': 'op', 'op': 'Const', 'value': int64_array([0])},
                                 'fill_value_data_ones': {'kind': 'data'},
                                 'broadcast': {'kind': 'op', 'op': 'Broadcast'},
                                 'broadcast_data': {'kind': 'data'},

                                 'fill_value_ones_2': {'kind': 'op', 'op': 'Const', 'value': int64_array([1])},
                                 'fill_value_data_ones_2': {'kind': 'data'},

                                 'memory_in': {'kind': 'op', 'op': 'ReadValue', 'shape': int64_array([5])},
                                 'memory_in_data': {'kind': 'data'},
                                 'memory_out': {'kind': 'op', 'op': 'Assign', 'shape': int64_array([5])},
                                 'memory_out_data': {'kind': 'data'},
                                 'result': {'kind': 'op', 'op': 'Result'},
                                 'crop_in': {'kind': 'op', 'op': 'Crop', 'axis': 1, 'offset': 1, 'dim': 4},
                                 'crop_in_data': {'kind': 'data'},
                                 'crop_out': {'kind': 'op', 'op': 'Crop', 'axis': 1, 'offset': 0, 'dim': 1},
                                 'crop_out_data': {'kind': 'data'},
                                 'equal': {'kind': 'op', 'op': 'Equal'},
                                 'equal_data': {'kind': 'data'},
                                 'select': {'kind': 'op', 'op': 'Select'},
                                 'select_out_data': {'kind': 'data', 'shape': [1, 26]},
                                 'const_0': {'kind': 'op', 'op': 'Const'},
                                 'const_0_data': {'kind': 'data'},
                                 'concat': {'kind': 'op', 'op': 'Concat'},
                                 'concat_data': {'kind': 'data'},

                                 'placeholder_data_2': {'kind': 'data', 'shape': [1, 26]},
                                 'memory': {'kind': 'op', 'op': 'Assign'},
                                 },
                                [('placeholder_1', 'placeholder_data_1'),
                                 ('placeholder_data_1', 'splice_1'), ('splice_1', 'splice_data_1'),
                                 ('splice_data_1', 'placeholder_2'), ('placeholder_2', 'placeholder_data_2'),
                                 ('placeholder_data_2', 'select', {'in': 1}),

                                 ('fill_value', 'fill_value_data'),
                                 ('fill_value_data', 'memory_in'),

                                 ('memory_in', 'memory_in_data'), ('memory_in_data', 'crop_in'),
                                 ('crop_in', 'crop_in_data'), ('crop_in_data', 'concat', {'in': 0}),

                                 ('fill_value_ones_2', 'fill_value_data_ones_2'),
                                 ('fill_value_data_ones_2', 'concat', {'in': 1}),

                                 ('concat', 'concat_data'), ('concat_data', 'memory_out'),
                                 ('memory_out', 'memory_out_data'), ('memory_out_data', 'result'),
                                 ('concat_data', 'crop_out'), ('crop_out', 'crop_out_data'),
                                 ('crop_out_data', 'equal', {'in': 1}), ('fill_value_data_ones_2', 'equal', {'in': 0}),
                                 ('equal', 'equal_data'),
                                 ('equal_data', 'select', {'in': 0}),

                                 ('placeholder_data_2', 'shape'), ('shape', 'shape_data'),
                                 ('shape_data', 'crop_batch'), ('crop_batch', 'crop_batch_data'),
                                 ('crop_batch_dim', 'crop_batch_dim_data'),
                                 ('crop_batch_dim_data', 'crop_batch', {'in': 1}),
                                 ('second_dim', 'second_dim_data'), ('second_dim_data', 'gather_shape', {'in': 1}),
                                 ('crop_batch_data', 'gather_shape', {'in': 0}), ('gather_shape', 'gather_shape_data'),
                                 ('fill_value_ones', 'fill_value_data_ones'),
                                 ('fill_value_data_ones', 'broadcast', {'in': 0}),
                                 ('gather_shape_data', 'broadcast', {'in': 1}), ('broadcast', 'broadcast_data'),
                                 ('broadcast_data', 'select', {'in': 2}),

                                 ('select', 'select_out_data'),
                                 ('select_out_data', 'memory')
                                 ],
                                nodes_with_edges_only=True
                                )

        (flag, resp) = compare_graphs(graph, ref_graph, 'memory')
        self.assertTrue(flag, resp)

    # graph contains 1 splice with context length 5 on the path to memory and 1 out of path,
    # should be inserted select with memory as counter with length 5
    def test_insert_select_2(self):
        graph = build_graph({
                             'placeholder_1': {'kind': 'op', 'op': 'Parameter'},
                             'placeholder_data_1': {'kind': 'data', 'shape': [1, 13]},
                             'splice_1': {'kind': 'op', 'op': 'Splice', 'context': np.array([-2, -1, 0, 1, 2])},
                             'splice_data_1': {'kind': 'data', 'shape': [1, 65]},
                             'splice_2': {'kind': 'op', 'op': 'Splice', 'context': np.array([-1, 0, 1])},
                             'splice_data_2': {'kind': 'data', 'shape': [1, 39]},
                             'placeholder_2': {'kind': 'op', 'op': None},
                             'placeholder_data_2': {'kind': 'data', 'shape': [1, 26]},
                             'memory': {'kind': 'op', 'op': 'Assign'},
                             },
                            [('placeholder_1', 'placeholder_data_1'),
                             ('placeholder_data_1', 'splice_1'), ('splice_1', 'splice_data_1'),
                             ('placeholder_data_1', 'splice_2'), ('splice_2', 'splice_data_2'),
                             ('splice_data_1', 'placeholder_2'), ('placeholder_2', 'placeholder_data_2'),
                             ('placeholder_data_2', 'memory')
                             ],
                            nodes_with_edges_only=True)
        AddSelectBeforeMemoryNodePattern().find_and_replace_pattern(graph)
        ref_graph = build_graph({
                                 'placeholder_1': {'kind': 'op', 'op': 'Parameter'},
                                 'placeholder_data_1': {'kind': 'data', 'shape': [1, 13]},
                                 'splice_1': {'kind': 'op', 'op': 'Splice', 'context': np.array([-2, -1, 0, 1, 2])},
                                 'splice_data_1': {'kind': 'data', 'shape': [1, 65]},
                                 'splice_2': {'kind': 'op', 'op': 'Splice', 'context': np.array([-1, 0, 1])},
                                 'splice_data_2': {'kind': 'data', 'shape': [1, 39]},
                                 'placeholder_2': {'kind': 'op', 'op': None},

                                 'fill_value': {'kind': 'op', 'op': 'Const', 'value': int64_array([0])},
                                 'fill_value_data': {'kind': 'data'},

                                 'shape': {'kind': 'op', 'op': 'ShapeOf'},
                                 'shape_data': {'kind': 'data'},
                                 'crop_batch': {'kind': 'op', 'op': 'Crop', 'offset': int64_array([0])},
                                 'crop_batch_data': {'kind': 'data'},
                                 'crop_batch_dim': {'kind': 'op', 'op': 'Const', 'value': int64_array([1])},
                                 'crop_batch_dim_data': {'kind': 'data'},
                                 'second_dim': {'kind': 'op', 'op': 'Const', 'value': int64_array([5])},
                                 'second_dim_data': {'kind': 'data'},
                                 'gather_shape': {'kind': 'op', 'op': 'Concat'},
                                 'gather_shape_data': {'kind': 'data'},
                                 'fill_value_ones': {'kind': 'op', 'op': 'Const', 'value': int64_array([0])},
                                 'fill_value_data_ones': {'kind': 'data'},
                                 'broadcast': {'kind': 'op', 'op': 'Broadcast'},
                                 'broadcast_data': {'kind': 'data'},

                                 'fill_value_ones_2': {'kind': 'op', 'op': 'Const', 'value': int64_array([1])},
                                 'fill_value_data_ones_2': {'kind': 'data'},

                                 'memory_in': {'kind': 'op', 'op': 'ReadValue', 'shape': int64_array([5])},
                                 'memory_in_data': {'kind': 'data'},
                                 'memory_out': {'kind': 'op', 'op': 'Assign', 'shape': int64_array([5])},
                                 'memory_out_data': {'kind': 'data'},
                                 'result': {'kind': 'op', 'op': 'Result'},
                                 'crop_in': {'kind': 'op', 'op': 'Crop', 'axis': 1, 'offset': 1, 'dim': 4},
                                 'crop_in_data': {'kind': 'data'},
                                 'crop_out': {'kind': 'op', 'op': 'Crop', 'axis': 1, 'offset': 0, 'dim': 1},
                                 'crop_out_data': {'kind': 'data'},
                                 'equal': {'kind': 'op', 'op': 'Equal'},
                                 'equal_data': {'kind': 'data'},
                                 'select': {'kind': 'op', 'op': 'Select'},
                                 'select_out_data': {'kind': 'data', 'shape': [1, 26]},
                                 'const_0': {'kind': 'op', 'op': 'Const'},
                                 'const_0_data': {'kind': 'data'},
                                 'concat': {'kind': 'op', 'op': 'Concat'},
                                 'concat_data': {'kind': 'data'},

                                 'placeholder_data_2': {'kind': 'data', 'shape': [1, 26]},
                                 'memory': {'kind': 'op', 'op': 'Assign'},
                                 },
                                [('placeholder_1', 'placeholder_data_1'),
                                 ('placeholder_data_1', 'splice_1'), ('splice_1', 'splice_data_1'),
                                 ('placeholder_data_1', 'splice_2'), ('splice_2', 'splice_data_2'),
                                 ('splice_data_1', 'placeholder_2'), ('placeholder_2', 'placeholder_data_2'),
                                 ('placeholder_data_2', 'select', {'in': 1}),

                                 ('fill_value', 'fill_value_data'), ('fill_value_data', 'memory_in'),

                                 ('memory_in', 'memory_in_data'), ('memory_in_data', 'crop_in'),
                                 ('crop_in', 'crop_in_data'), ('crop_in_data', 'concat', {'in': 0}),

                                 ('fill_value_ones_2', 'fill_value_data_ones_2'),
                                 ('fill_value_data_ones_2', 'concat', {'in': 1}),

                                 ('concat', 'concat_data'), ('concat_data', 'memory_out'),
                                 ('memory_out', 'memory_out_data'), ('memory_out_data', 'result'),
                                 ('concat_data', 'crop_out'), ('crop_out', 'crop_out_data'),
                                 ('crop_out_data', 'equal', {'in': 1}), ('fill_value_data_ones_2', 'equal', {'in': 0}),
                                 ('equal', 'equal_data'),
                                 ('equal_data', 'select', {'in': 0}),

                                 ('placeholder_data_2', 'shape'), ('shape', 'shape_data'),
                                 ('shape_data', 'crop_batch'), ('crop_batch', 'crop_batch_data'),
                                 ('crop_batch_dim', 'crop_batch_dim_data'),
                                 ('crop_batch_dim_data', 'crop_batch', {'in': 1}),
                                 ('second_dim', 'second_dim_data'), ('second_dim_data', 'gather_shape', {'in': 1}),
                                 ('crop_batch_data', 'gather_shape', {'in': 0}), ('gather_shape', 'gather_shape_data'),
                                 ('fill_value_ones', 'fill_value_data_ones'),
                                 ('fill_value_data_ones', 'broadcast', {'in': 0}),
                                 ('gather_shape_data', 'broadcast', {'in': 1}), ('broadcast', 'broadcast_data'),
                                 ('broadcast_data', 'select', {'in': 2}),

                                 ('select', 'select_out_data'),
                                 ('select_out_data', 'memory')
                                 ],
                                nodes_with_edges_only=True
                                )
        (flag, resp) = compare_graphs(graph, ref_graph, 'memory')
        self.assertTrue(flag, resp)

    # graph contains 2 splices with sum context length 8 on the path to memory,
    # should be inserted select with memory as counter with length 7
    def test_insert_select_3(self):
        graph = build_graph({
                             'placeholder_1': {'kind': 'op', 'op': 'Parameter'},
                             'placeholder_data_1': {'kind': 'data', 'shape': [1, 13]},
                             'splice_1': {'kind': 'op', 'op': 'Splice', 'context': np.array([-2, -1, 0, 1, 2])},
                             'splice_data_1': {'kind': 'data', 'shape': [1, 65]},
                             'splice_2': {'kind': 'op', 'op': 'Splice', 'context': np.array([-1, 0, 1])},
                             'splice_data_2': {'kind': 'data', 'shape': [1, 39]},
                             'placeholder_2': {'kind': 'op', 'op': None},
                             'placeholder_data_2': {'kind': 'data', 'shape': [1, 26]},
                             'memory': {'kind': 'op', 'op': 'Assign', 'index': 0},
                             },
                            [('placeholder_1', 'placeholder_data_1'),
                             ('placeholder_data_1', 'splice_1'), ('splice_1', 'splice_data_1'),
                             ('splice_data_1', 'splice_2'), ('splice_2', 'splice_data_2'),
                             ('splice_data_2', 'placeholder_2'), ('placeholder_2', 'placeholder_data_2'),
                             ('placeholder_data_2', 'memory')
                             ],
                            nodes_with_edges_only=True)
        AddSelectBeforeMemoryNodePattern().find_and_replace_pattern(graph)
        ref_graph = build_graph({
                                 'placeholder_1': {'kind': 'op', 'op': 'Parameter'},
                                 'placeholder_data_1': {'kind': 'data', 'shape': [1, 13]},
                                 'splice_1': {'kind': 'op', 'op': 'Splice', 'context': np.array([-2, -1, 0, 1, 2])},
                                 'splice_data_1': {'kind': 'data', 'shape': [1, 65]},
                                 'splice_2': {'kind': 'op', 'op': 'Splice', 'context': np.array([-1, 0, 1])},
                                 'splice_data_2': {'kind': 'data', 'shape': [1, 39]},
                                 'placeholder_2': {'kind': 'op', 'op': None},

                                 'fill_value': {'kind': 'op', 'op': 'Const', 'value': int64_array([0])},
                                 'fill_value_data': {'kind': 'data'},

                                 'shape': {'kind': 'op', 'op': 'ShapeOf'},
                                 'shape_data': {'kind': 'data'},
                                 'crop_batch': {'kind': 'op', 'op': 'Crop', 'offset': int64_array([0])},
                                 'crop_batch_data': {'kind': 'data'},
                                 'crop_batch_dim': {'kind': 'op', 'op': 'Const', 'value': int64_array([1])},
                                 'crop_batch_dim_data': {'kind': 'data'},
                                 'second_dim': {'kind': 'op', 'op': 'Const', 'value': int64_array([5])},
                                 'second_dim_data': {'kind': 'data'},
                                 'gather_shape': {'kind': 'op', 'op': 'Concat'},
                                 'gather_shape_data': {'kind': 'data'},
                                 'fill_value_ones': {'kind': 'op', 'op': 'Const', 'value': int64_array([0])},
                                 'fill_value_data_ones': {'kind': 'data'},
                                 'broadcast': {'kind': 'op', 'op': 'Broadcast'},
                                 'broadcast_data': {'kind': 'data'},

                                 'fill_value_ones_2': {'kind': 'op', 'op': 'Const', 'value': int64_array([1])},
                                 'fill_value_data_ones_2': {'kind': 'data'},

                                 'memory_in': {'kind': 'op', 'op': 'ReadValue', 'shape': int64_array([5])},
                                 'memory_in_data': {'kind': 'data'},
                                 'memory_out': {'kind': 'op', 'op': 'Assign', 'shape': int64_array([5])},
                                 'memory_out_data': {'kind': 'data'},
                                 'result': {'kind': 'op', 'op': 'Result'},
                                 'crop_in': {'kind': 'op', 'op': 'Crop', 'axis': 1, 'offset': 1, 'dim': 4},
                                 'crop_in_data': {'kind': 'data'},
                                 'crop_out': {'kind': 'op', 'op': 'Crop', 'axis': 1, 'offset': 0, 'dim': 1},
                                 'crop_out_data': {'kind': 'data'},
                                 'equal': {'kind': 'op', 'op': 'Equal'},
                                 'equal_data': {'kind': 'data'},
                                 'select': {'kind': 'op', 'op': 'Select'},
                                 'select_out_data': {'kind': 'data', 'shape': [1, 26]},
                                 'const_0': {'kind': 'op', 'op': 'Const'},
                                 'const_0_data': {'kind': 'data'},
                                 'concat': {'kind': 'op', 'op': 'Concat'},
                                 'concat_data': {'kind': 'data'},

                                 'placeholder_data_2': {'kind': 'data', 'shape': [1, 26]},
                                 'memory': {'kind': 'op', 'op': 'Assign', 'index': 0},
                                 },
                                [('placeholder_1', 'placeholder_data_1'),
                                 ('placeholder_data_1', 'splice_1'), ('splice_1', 'splice_data_1'),
                                 ('splice_data_1', 'splice_2'), ('splice_2', 'splice_data_2'),
                                 ('splice_data_2', 'placeholder_2'), ('placeholder_2', 'placeholder_data_2'),
                                 ('placeholder_data_2', 'select', {'in': 1}),

                                 ('fill_value', 'fill_value_data'), ('fill_value_data', 'memory_in'),

                                 ('memory_in', 'memory_in_data'), ('memory_in_data', 'crop_in'),
                                 ('crop_in', 'crop_in_data'), ('crop_in_data', 'concat', {'in': 0}),

                                 ('fill_value_ones_2', 'fill_value_data_ones_2'),
                                 ('fill_value_data_ones_2', 'concat', {'in': 1}),

                                 ('concat', 'concat_data'), ('concat_data', 'memory_out'),
                                 ('memory_out', 'memory_out_data'), ('memory_out_data', 'result'),
                                 ('concat_data', 'crop_out'), ('crop_out', 'crop_out_data'),
                                 ('crop_out_data', 'equal', {'in': 1}), ('fill_value_data_ones_2', 'equal', {'in': 0}),
                                 ('equal', 'equal_data'),
                                 ('equal_data', 'select', {'in': 0}),

                                 ('placeholder_data_2', 'shape'), ('shape', 'shape_data'),
                                 ('shape_data', 'crop_batch'), ('crop_batch', 'crop_batch_data'),
                                 ('crop_batch_dim', 'crop_batch_dim_data'),
                                 ('crop_batch_dim_data', 'crop_batch', {'in': 1}),
                                 ('second_dim', 'second_dim_data'), ('second_dim_data', 'gather_shape', {'in': 1}),
                                 ('crop_batch_data', 'gather_shape', {'in': 0}), ('gather_shape', 'gather_shape_data'),
                                 ('fill_value_ones', 'fill_value_data_ones'),
                                 ('fill_value_data_ones', 'broadcast', {'in': 0}),
                                 ('gather_shape_data', 'broadcast', {'in': 1}), ('broadcast', 'broadcast_data'),
                                 ('broadcast_data', 'select', {'in': 2}),

                                 ('select', 'select_out_data'),
                                 ('select_out_data', 'memory')
                                 ],
                                nodes_with_edges_only=True
                                )

        (flag, resp) = compare_graphs(graph, ref_graph, 'memory')
        self.assertTrue(flag, resp)
