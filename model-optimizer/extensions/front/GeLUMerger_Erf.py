"""
 Copyright (C) 2017-2021 Intel Corporation

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

import logging as log

from math import sqrt, fabs

from extensions.ops.gelu import GeLUOP
from mo.front.common.replacement import FrontReplacementPattern
from mo.graph.graph import Graph, rename_nodes
from mo.middle.pattern_match import apply_pattern


class GeLUMergerErf(FrontReplacementPattern):
    enabled = True

    def pattern1(self):
        # (0.5 * x) * (1 + erf(x / sqrt(2))
        return dict(
            nodes=[
                ('mul', dict(op='Mul')),
                ('mul0', dict(op='Mul')),
                ('div', dict(op='Div')),
                ('erf', dict(op='Erf')),
                ('add', dict(op='Add')),
                ('mul_param', dict(op='Const')),
                ('div_param', dict(op='Const')),
                ('add_param', dict(op='Const')),
            ],
            edges=[
                ('mul', 'mul0'),
                ('div', 'erf'),
                ('erf', 'add'),
                ('add', 'mul0'),
                ('mul_param', 'mul'),
                ('div_param', 'div'),
                ('add_param', 'add'),
            ])

    def pattern2(self):
        # 0.5 * (x * (1 + erf(x / sqrt(2)))
        return dict(
            nodes=[
                ('mul', dict(op='Mul')),
                ('mul0', dict(op='Mul')),
                ('div', dict(op='Div')),
                ('erf', dict(op='Erf')),
                ('add', dict(op='Add')),
                ('mul_param', dict(op='Const')),
                ('div_param', dict(op='Const')),
                ('add_param', dict(op='Const')),
            ],
            edges=[
                ('div', 'erf'),
                ('erf', 'add'),
                ('add', 'mul'),
                ('mul', 'mul0'),
                ('mul_param', 'mul0'),
                ('div_param', 'div'),
                ('add_param', 'add'),
            ])

    def pattern3(self):
        # x * (0.5 * (1 + erf(x / sqrt(2)))
        return dict(
            nodes=[
                ('mul', dict(op='Mul')),
                ('mul0', dict(op='Mul')),
                ('div', dict(op='Div')),
                ('erf', dict(op='Erf')),
                ('add', dict(op='Add')),
                ('mul_param', dict(op='Const')),
                ('div_param', dict(op='Const')),
                ('add_param', dict(op='Const')),
            ],
            edges=[
                ('div', 'erf'),
                ('erf', 'add'),
                ('add', 'mul'),
                ('mul', 'mul0'),
                ('mul_param', 'mul'),
                ('div_param', 'div'),
                ('add_param', 'add'),
            ])

    def find_and_replace_pattern(self, graph: Graph):
        log.info('Enabled GeLU Merger replacement for approximation with Erf')
        apply_pattern(graph, **self.pattern1(), action=self.replace_gelu)
        apply_pattern(graph, **self.pattern2(), action=self.replace_gelu)
        apply_pattern(graph, **self.pattern3(), action=self.replace_gelu)

    def replace_gelu(self, graph: Graph, match: dict):
        # Gaussian Error Linear Unit
        # f(x) = 0.5 * x * (1 + erf(x / sqrt(2))
        out_node = match['mul0']
        node_name = out_node.soft_get('name', out_node.id)
        div = match['div']
        inp_node = div.in_port(0).get_source().node
        inp_name = inp_node.soft_get('name', out_node.id)
        log.debug('Found potential Erf-based GeLU pattern after {} with name {}'.format(inp_node.op, inp_name))

        # take the values of the mul, add and div
        div_param = match['div_param']
        add_param = match['add_param']
        mul_param = match['mul_param']

        if add_param.value.size == 1 and mul_param.value.size == 1 and div_param.value.size == 1:
            mul_param = match['mul_param'].value.item()
            add_param = match['add_param'].value.item()
            div_param = match['div_param'].value.item()

            sqrt2 = sqrt(2.0)
            # check that the values match the approximation
            if fabs(div_param - sqrt2) < 1e-06 and mul_param == 0.5 and add_param == 1.0:
                log.debug('Confirmed Erf-based GELU pattern after {} with name {}'.format(inp_node.op, inp_name))
                gelu = GeLUOP(graph, dict(name=inp_name + '/GELU_', approximation='erf')).create_node()
                div.in_port(0).get_connection().set_destination(gelu.in_port(0))
                out_node.out_port(0).get_connection().set_source(gelu.out_port(0))
                rename_nodes([(out_node, node_name + '/TBD'), (gelu, node_name)])
