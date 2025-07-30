import ast
import copy
import re
import fitz
import sys
import os

sys.path.append(os.path.abspath('../..'))

from DrafterBench.utils.testf.test_types import (
    extrracted_anno,
    fontlist,
    TEXT_ALIGN_CENTER,
    TEXT_ALIGN_JUSTIFY,
    TEXT_ALIGN_RIGHT,
    TEXT_ALIGN_LEFT,
    fileobject,
)


align_list = [
    TEXT_ALIGN_CENTER,
    TEXT_ALIGN_LEFT,
    TEXT_ALIGN_RIGHT,
    TEXT_ALIGN_JUSTIFY,
    fitz.TEXT_ALIGN_CENTER,
    fitz.TEXT_ALIGN_JUSTIFY,
    fitz.TEXT_ALIGN_LEFT,
    fitz.TEXT_ALIGN_RIGHT,
    0,
    1,
    2,
    3,
    "center",
    "left",
    "right",
    "justify",
]

global taskinformation
taskinformation = []

tool_calling_format = {
    "tool_name": "tool_name",
    "arguments_value": [],
    "necessary_arguments": [],
    "transfered_arguments": [],
    "first_defined_arguments": [],
    "vaguly_defined_arguments": [],
    "save": False,
}


def convert_num(num_in_str):
    try:
        d = ast.literal_eval(num_in_str)
    except Exception as e:
        d = num_in_str
    return d


def validity_check(argu: any, tar_type: list):
    return True if type(argu) in tar_type else False


def doctrack(doc: any) -> fileobject:
    if not isinstance(doc, fileobject):
        doc = fileobject()
    filepath = doc.fileblock["filepath"]
    global taskinformation
    exsistfile = [x["filepath"] for x in taskinformation]
    if filepath not in exsistfile:
        taskinformation.append(doc.fileblock)
    return doc


def page_track(doc: fileobject, pagenumber: any = "Unknown"):
    exsist_pages = doc.fileblock["pages"]
    page = (
        pagenumber,
        (
            True
            if type(pagenumber) is int or pagenumber in ["missing", "Missing"]
            else False
        ),
    )
    if page in exsist_pages:
        page_index = exsist_pages.index(page)
    else:
        doc.fileblock["pages"].append(page)
        page_index = len(doc.fileblock["pages"]) - 1
    return page, page_index


def rect_track(doc: fileobject, clip: any = "Unknown"):
    if isinstance(clip, extrracted_anno):
        rect = clip
        rect_infro = (
            str(clip.doc[0])
            + "-"
            + str(clip.page[0])
            + "-"
            + str(clip.order_or_annocolor[0]),
            (
                True
                if all([clip.doc[1], clip.page[1], clip.order_or_annocolor[1]])
                else False
            ),
        )
    elif (
        type(clip) is list
        and type(clip[0]) is dict
        and list(clip[0].keys()) == ["data_name", "position_arguments"]
    ):
        rect = (
            clip[0]["position_arguments"][0][1],
            clip[0]["position_arguments"][1][1],
            clip[0]["position_arguments"][2][1],
        )
        rect_infro = (
            str(rect[0][0]) + "-" + str(rect[1][0]) + "-" + str(rect[2][0]),
            True if all([rect[0][1], rect[1][1], rect[2][1]]) else False,
        )
    else:
        rect = extrracted_anno()
        rect_infro = (
            extrracted_anno().doc[0]
            + "-"
            + extrracted_anno().page[0]
            + "-"
            + extrracted_anno().order_or_annocolor[0],
            False,
        )
    if rect in doc.fileblock["annotation"]:
        rect_index = doc.fileblock["annotation"].index(rect)
    else:
        doc.fileblock["annotation"].append(rect)
        rect_index = len(doc.fileblock["annotation"]) - 1
    return rect_infro, rect_index


def class_track(doc: fileobject, class_block: dict, instance: str):
    exsist_instances = [
        {k: v for k, v in x.items() if k != "tool_callings"}
        for x in doc.fileblock[instance]
        if type(x) is dict
    ]
    block = {k: v for k, v in class_block.items() if k != "tool_callings"}
    if block in exsist_instances:
        tracked_index = exsist_instances.index(block)
    else:
        doc.fileblock[instance].append(class_block)
        tracked_index = len(doc.fileblock[instance]) - 1
    return doc.fileblock[instance][tracked_index]


def tool_track(class_block: dict, tool_block: dict):
    exsist_tools = class_block["tool_callings"]
    if tool_block in exsist_tools:
        tracked_index = class_block["tool_callings"].index(tool_block)
    else:
        class_block["tool_callings"].append(tool_block)
        tracked_index = len(class_block["tool_callings"]) - 1
    return class_block["tool_callings"][tracked_index]


def tool_calling_update(tool_name: str, class_block: dict, tool_block=None):
    tool_block = copy.deepcopy(tool_calling_format) if not tool_block else tool_block
    tool_block["tool_name"] = tool_name
    tool_track(class_block, tool_block)


def open(filepath: any = "Unknow"):
    doc = fileobject(filepath)
    taskinformation.append(doc.fileblock)
    return doc


class basic:
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
    ):
        self.doc = doctrack(doc)
        self.page, self.page_index = page_track(self.doc, pagenumber)


class extractanno:
    def __init__(
        self, doc: any = "Unknow", pagenumber: any = "Unknow", annocolor: any = "Unknow"
    ):
        self.doc = doctrack(doc)
        self.page = (pagenumber, True if type(pagenumber) in [int] else False)
        self.annoclolor = (annocolor, True if type(annocolor) is str else False)
        self.extractor_block = {
            "operation": "instantiate_extractor",
            "arguments_value": [("doc", self.doc.fileblock["filepath"])],
            "necessary_arguments": ["doc"],
            "transfered_arguments": ["doc"],
            "first_defined_arguments": [],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.extractor_block = class_track(self.doc, self.extractor_block, "extractor")

    def getclip_rfpoint(
        self, pagenumber: any = "Unknow", rectangleorder: any = "Unknow"
    ):
        page = (pagenumber, True if type(pagenumber) is int else False)
        rect = (rectangleorder, True if type(rectangleorder) is int else False)
        tool_block = copy.deepcopy(tool_calling_format)
        key_list = ["page", "order"]
        argulist = [("page", page), ("order", rect)]
        tool_block["arguments_value"] = argulist
        tool_block["first_defined_arguments"].extend(key_list)
        tool_calling_update("exract_rect", self.extractor_block, tool_block)
        extracted_rectangle_rfpoint = extrracted_anno(
            self.doc.fileblock["filepath"], page, rect
        )
        return extracted_rectangle_rfpoint, extracted_rectangle_rfpoint

    def anno(self):
        tool_block = copy.deepcopy(tool_calling_format)
        key_list = ["page", "order"]
        argulist = [("page", self.page), ("order", self.annoclolor)]
        tool_block["arguments_value"] = argulist
        tool_block["first_defined_arguments"].extend(key_list)
        tool_calling_update("exract_anno", self.extractor_block, tool_block)
        extracteddrawing = extrracted_anno(
            self.doc.fileblock["filepath"], self.page, self.annoclolor
        )
        selected_vectors = [
            {
                "data_name": "vectors",
                "position_arguments": [
                    ("doc", self.doc.fileblock["filepath"]),
                    ("page", self.page),
                    ("clip", self.annoclolor),
                ],
            }
        ]
        selected_vectors[0]["data_name"] = "drawings"
        return selected_vectors


class basic_selector(basic):
    def __init__(
        self, doc: any = "Unknown", pagenumber: any = "Unknow", clip: any = "Uknown"
    ):
        super().__init__(doc, pagenumber)
        self.rect, self.rect_index = rect_track(self.doc, clip)
        self.selector_block = {
            "operation": "instantiate_selector",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
            ],
            "necessary_arguments": ["doc", "page", "clip"],
            "transfered_arguments": ["doc", "page", "clip"],
            "first_defined_arguments": [],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.selected_vectors = [
            {
                "data_name": "all_lines",
                "position_arguments": [
                    ("doc", self.doc.fileblock["filepath"]),
                    ("page", self.page),
                    ("clip", self.rect),
                ],
            }
        ]

    def mode1_drawings_Window_Cover_Enclosure(self):
        tool_calling_update("select_mode1_drawings", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode1_drawings"
        return selected_vectors

    def mode2_drawings_Cross_Touch_Intersect(self):
        tool_calling_update("select_mode2_drawings", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode2_drawings"
        return selected_vectors

    def mode1_lines_Window_Cover_Enclosure(self):
        tool_calling_update("select_mode1_lines", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode1_lines"
        return selected_vectors

    def mode2_lines_Cross_Touch_Intersect(self):
        tool_calling_update("select_mode2_lines", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode2_lines"
        return selected_vectors

    def mode1_rebars_Window_Cover_Enclosure(self):
        tool_calling_update("select_mode1_rebars", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode1_rebars"
        return selected_vectors

    def mode2_rebars_Cross_Touch_Intersect(self):
        tool_calling_update("select_mode2_rebars", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode2_rebars"
        return selected_vectors

    def mode1_columns_Window_Cover_Enclosure(self):
        tool_calling_update("select_mode1_columns", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode1_columns"
        return selected_vectors

    def mode2_columns_Cross_Touch_Intersect(self):
        tool_calling_update("select_mode2_columns", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "mode2_columns"
        return selected_vectors


class selector(basic_selector):
    def __init__(
        self, doc: any = "Unknown", pagenumber: any = "Unknow", clip: any = "Uknown"
    ):
        super().__init__(doc, pagenumber, clip)
        self.selector_block = class_track(self.doc, self.selector_block, "selector")
        self.selected_lines = self.selected_vectors


class select_from_drawings(basic_selector):
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
        cdrawings: any = "Unknown",
    ):
        super().__init__(doc, pagenumber, cdrawings)
        self.anno, self.anno_index = rect_track(self.doc, cdrawings)
        self.selector_block = {
            "operation": "instantiate_selector",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("cdrawings", self.anno),
            ],
            "necessary_arguments": ["doc", "page", "cdrawings"],
            "transfered_arguments": ["doc", "page", "cdrawings"],
            "first_defined_arguments": [],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.selected_vectors = [
            {
                "data_name": "vectors",
                "position_arguments": [
                    ("doc", self.doc.fileblock["filepath"]),
                    ("page", self.page),
                    ("clip", self.anno),
                ],
            }
        ]
        self.selector_block = class_track(
            self.doc, self.selector_block, "select_from_drawings"
        )

    def get_rebar_column(self):
        tool_calling_update("select_rebar_and_columns", self.selector_block)
        selected_vectors = copy.deepcopy(self.selected_vectors)
        selected_vectors[0]["data_name"] = "rebars_and_columns"
        return selected_vectors


class manipulate_text(basic):
    def __init__(
        self,
        doc="Unknown",
        pagenumber="Unknown",
        clip="Unknown",
        text="Unknown",
        font=None,
        fontsize=None,
        textcolor=None,
        fill=None,
        rotate=None,
        align=None,
    ):
        super().__init__(doc, pagenumber)
        self.rect, _ = rect_track(self.doc, clip)
        self._text = (text, validity_check(text, [str]))
        self.font = (font, True if font in fontlist else False)
        self.fontsize = (fontsize, validity_check(fontsize, [int]))
        self.textcolor = (textcolor, validity_check(textcolor, [str]))
        self.fill = (fill, validity_check(fill, [str]))
        self.rotate = (rotate, validity_check(rotate, [int, float]))
        self.align = (align, True if align in align_list else False)
        self.text_manipulator_block = {
            "operation": "instantiate_text_manipulator",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
                ("text", self._text),
                ("font", self.font),
                ("fontsize", self.fontsize),
                ("textcolor", self.textcolor),
                ("fill", self.fill),
                ("rotate", self.rotate),
                ("align", self.align),
            ],
            "necessary_arguments": ["doc", "page", "clip", "text"],
            "transfered_arguments": ["doc", "page", "clip"],
            "first_defined_arguments": [
                "text",
                "font",
                "fontsize",
                "textcolor",
                "fill",
                "rotate",
                "align",
            ],
            "vaguly_defined_arguments": [
                "font",
                "fontsize",
                "textcolor",
                "fill",
                "rotate",
                "align",
            ],
            "tool_callings": [],
        }
        self.text_manipulator_block = class_track(
            self.doc, self.text_manipulator_block, "change_maker"
        )

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, te):
        self._text = (te, validity_check(te, [str]))
        self._update()

    def _update(self):
        updated_text = ("text", self._text)
        self.text_manipulator_block["arguments_value"] = [
            updated_text if x[0] == "text" else x
            for x in self.text_manipulator_block["arguments_value"]
        ]

    def addtext(self):
        tool_calling_update("add_text", self.text_manipulator_block)
        return self.doc

    def gethortext(self):
        tool_calling_update("get_hor_text", self.text_manipulator_block)
        return "horizontal_text"

    def getvertext(self):
        tool_calling_update("get_ver_text", self.text_manipulator_block)
        return "vertical_text"

    def deletetext(self, deltex=None):
        tool_block = copy.deepcopy(tool_calling_format)
        argulist = [
            ("deltex", (deltex, True if not deltex or type(deltex) is str else False))
        ]
        tool_block["arguments_value"] = argulist
        tool_block["first_defined_arguments"].append("deltex")
        tool_calling_update("delete_text", self.text_manipulator_block, tool_block)
        return self.text[0]

    def replacetext(self, retext=None, totext=None):
        tool_block = copy.deepcopy(tool_calling_format)
        key_list = ["retext", "totext"]
        argulist = [
            ("retext", (retext, validity_check(retext, [str]))),
            ("totext", (totext, validity_check(totext, [str]))),
        ]
        tool_block["arguments_value"] = argulist
        tool_block["necessary_arguments"].append("totext")
        tool_block["first_defined_arguments"].extend(key_list)
        tool_calling_update("replace_text", self.text_manipulator_block, tool_block)
        return self.text[0]


class extract_table(basic):
    def __init__(
        self, doc: any = "Unknown", pagenumber: any = "Unknow", clip: any = "Uknown"
    ):
        super().__init__(doc, pagenumber)
        self.rect, self.rect_index = rect_track(self.doc, clip)
        self.table_extractor_block = {
            "operation": "instantiate_table_extractor",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
            ],
            "necessary_arguments": ["doc", "page", "clip"],
            "transfered_arguments": ["doc", "page", "clip"],
            "first_defined_arguments": [],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.data = [
            [
                {
                    "data_name": "table_data",
                    "position_arguments": [
                        ("doc", self.doc.fileblock["filepath"]),
                        ("page", self.page),
                        ("clip", self.rect),
                    ],
                }
            ]
        ]
        self.table_extractor_block = class_track(
            self.doc, self.table_extractor_block, "table_extractor"
        )


def data_arrange_check(data):
    if data:
        format_check = (
            [True if not x or type(x) is list else False for x in data]
            if type(data) is list
            else [False]
        )
        value_check = (
            [[convert_num(y) for y in x] if type(x) is list else x for x in data]
            if type(data) is list
            else [False]
        )
    else:
        format_check = [None]
        value_check = None
    return (value_check, True if all(format_check) else False)


class manipulate_table(basic):
    def __init__(
        self,
        doc="Unknown",
        pagenumber="Unknown",
        clip="Unknown",
        data="Unknown",
        arrange=None,
        font=None,
        fontsize=None,
        borderwidth=None,
        align=None,
    ):
        super().__init__(doc, pagenumber)
        self.rect, self.rect_index = rect_track(self.doc, clip)
        self.data = data_arrange_check(data)
        self.arrange = data_arrange_check(arrange)
        self.font = (font, True if font in fontlist else False)
        self.font_size = (fontsize, validity_check(fontsize, [int]))
        self.border_width = (borderwidth, validity_check(borderwidth, [int, float]))
        self.align = (
            align,
            True if align in ["center", "left", "right", "justify"] else False,
        )
        self.table_manipulator_block = {
            "operation": "instantiate_table_manipulator",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
                ("data", self.data),
                ("arrange", self.arrange),
                ("font", self.font),
                ("font_size", self.font_size),
                ("border_width", self.border_width),
                ("align", self.align),
            ],
            "necessary_arguments": ["doc", "page", "clip", "data"],
            "transfered_arguments": ["doc", "page", "clip"],
            "first_defined_arguments": [
                "arrange",
                "font",
                "font_size",
                "border_width",
                "align",
            ],
            "vaguly_defined_arguments": ["font", "font_size", "border_width", "align"],
            "tool_callings": [],
        }
        try:
            if type(self.data[0][0]) is dict:
                self.table_manipulator_block["transfered_arguments"].append("data")
            else:
                self.table_manipulator_block["first_defined_arguments"].append("data")
        except Exception as e:
            self.table_manipulator_block["first_defined_arguments"].append("data")
        self.table_manipulator_block = class_track(
            self.doc, self.table_manipulator_block, "change_maker"
        )

    def addtable(self):
        tool_calling_update("add_table", self.table_manipulator_block)
        return self.doc

    def cuttable(self, delrow=None, delcolumn=None):
        tool_block = copy.deepcopy(tool_calling_format)
        key_list = ["delrow", "delcolumn"]
        argulist = [
            ("delrow", (delrow, validity_check(delrow, [list]))),
            ("delcolumn", (delcolumn, validity_check(delcolumn, [list]))),
        ]
        tool_block["arguments_value"] = argulist
        tool_block["first_defined_arguments"].extend(key_list)
        tool_calling_update("cut_table", self.table_manipulator_block, tool_block)
        return self.data

    def emptytable(self, startcell=None, endcell=None):
        tool_block = copy.deepcopy(tool_calling_format)
        key_list = ["start_cell", "end_cell"]
        argulist = [
            ("start_cell", (startcell, validity_check(startcell, [list]))),
            ("end_cell", (endcell, validity_check(endcell, [list]))),
        ]
        tool_block["arguments_value"] = argulist
        tool_block["first_defined_arguments"].extend(key_list)
        tool_calling_update("empty_table", self.table_manipulator_block, tool_block)
        return self.data

    def modifytable(self, startcell=None, endcell=None, repdata="Unknown"):
        tool_block = copy.deepcopy(tool_calling_format)
        key_list = ["start_cell", "end_cell", "rep_data"]
        argulist = [
            ("start_cell", (startcell, validity_check(startcell, [list]))),
            ("end_cell", (endcell, validity_check(endcell, [list]))),
            ("rep_data", (repdata, validity_check(repdata, [list]))),
        ]
        tool_block["arguments_value"] = argulist
        tool_block["necessary_arguments"].append("rep_data")
        tool_block["first_defined_arguments"].extend(key_list)
        tool_calling_update("modify_table", self.table_manipulator_block, tool_block)
        return self.data


def drawing_list_check(list_of_draw):
    draw_chcek = (
        [
            (
                True
                if type(x) is dict
                and list(x.keys()) == ["data_name", "position_arguments"]
                else False
            )
            for x in list_of_draw
        ]
        if type(list_of_draw) is list
        else [False]
    )
    return (copy.deepcopy(list_of_draw), True if all(draw_chcek) else False)


class draw_drawer(basic):
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
        listofcdraw: any = "Unknown",
    ):
        super().__init__(doc, pagenumber)
        self.listofdraw = drawing_list_check(listofcdraw)
        self.drawer_block = {
            "operation": "instantiate_drawer",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("listofdraw", self.listofdraw),
            ],
            "necessary_arguments": ["doc", "page", "listofdraw"],
            "transfered_arguments": ["doc", "page", "listofdraw"],
            "first_defined_arguments": [],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.drawer_block = class_track(self.doc, self.drawer_block, "change_maker")

    def delete_draw(self):
        tool_calling_update("delete_drawings", self.drawer_block)
        return self.doc


class delete(basic):
    def __init__(
        self, doc: any = "Unknown", pagenumber: any = "Unknown", clip: any = "Unknown"
    ):
        super().__init__(doc, pagenumber)
        self.rect, self.rect_index = rect_track(self.doc, clip)
        self.cleaner_block = {
            "operation": "instantiate_cleaner",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
            ],
            "necessary_arguments": ["doc", "page", "clip"],
            "transfered_arguments": ["doc", "page", "clip"],
            "first_defined_arguments": [],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.cleaner_block = class_track(self.doc, self.cleaner_block, "change_maker")

    def applydelete(self):
        tool_calling_update("clean_drawings", self.cleaner_block)
        return self.doc


class repairer(basic):
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
        clip: any = "Unknown",
        sel_drawings: any = "Unknown",
        cdrawings: any = "Unknown",
    ):
        super().__init__(doc, pagenumber)
        self.rect, self.rect_index = rect_track(self.doc, clip)
        self.sel_drawings = drawing_list_check(sel_drawings)
        self.cdrawings = drawing_list_check(cdrawings)
        self.repairer_block = {
            "operation": "instantiate_repairer",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
                ("sel_drawings", self.sel_drawings),
                ("cdrawings", self.cdrawings),
            ],
            "necessary_arguments": ["doc", "page", "clip", "sel_drawings", "cdrawings"],
            "transfered_arguments": [
                "doc",
                "page",
                "clip",
                "sel_drawings",
                "cdrawings",
            ],
            "first_defined_arguments": [],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.repairer_block = class_track(
            self.doc, self.repairer_block, "post_change_maker"
        )

    def del_repair(self):
        tool_calling_update("repair_drawings", self.repairer_block)
        return self.doc


def dashes_check(dashes: any) -> tuple:
    dashchecker = re.compile(r"\s*(\[\s*\d*\s+\d*\s*\]\s*\d*)")
    dashvalue = dashchecker.search(dashes) if dashes else None
    dash = dashvalue.group(0) if dashvalue else None
    return (dash, True if dash else False)


class manipulate_draw(basic):
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
        sel_drawings: any = "Unknown",
        fillcolor=None,
        drwcolor=None,
        dashes=None,
        closePath=None,
        lineJoin=None,
        lineCap=None,
        width=None,
    ):
        super().__init__(doc, pagenumber)
        self.sel_drawings = drawing_list_check(sel_drawings)
        self.fillcolor = (fillcolor, validity_check(fillcolor, [str]))
        self.drwcolor = (drwcolor, validity_check(drwcolor, [str]))
        self.dashes = dashes_check(dashes)
        self.closePath = (closePath, validity_check(closePath, [bool]))
        self.lineJoin = (lineJoin, True if lineJoin in [0, 1, 2] else False)
        self.lineCap = (lineCap, True if lineCap in [0, 1, 2] else False)
        self.width = (width, validity_check(width, [int, float]))
        self.drawing_manipulator_block = {
            "operation": "instantiate_drawing_manipulator",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("sel_drawings", self.sel_drawings),
                ("fillcolor", self.fillcolor),
                ("drwcolor", self.drwcolor),
                ("dashes", self.dashes),
                ("closePath", self.closePath),
                ("lineJoin", self.lineJoin),
                ("lineCap", self.lineCap),
                ("width", self.width),
            ],
            "necessary_arguments": ["doc", "page", "sel_drawings"],
            "transfered_arguments": ["doc", "page", "sel_drawings"],
            "first_defined_arguments": [
                "fillcolor",
                "drwcolor",
                "dashes",
                "closePath",
                "lineJoin",
                "lineCap",
                "width",
            ],
            "vaguly_defined_arguments": [
                "fillcolor",
                "drwcolor",
                "dashes",
                "closePath",
                "lineJoin",
                "lineCap",
                "width",
            ],
            "tool_callings": [],
        }
        self.drawing_manipulator_block = class_track(
            self.doc, self.drawing_manipulator_block, "change_maker"
        )

    def update_draw(self):
        tool_calling_update("update_drawings", self.drawing_manipulator_block)
        return self.doc

    def add_standrawing(self):
        tool_calling_update("add_standrawings", self.drawing_manipulator_block)
        return self.doc


def missing_structure(missing_information):
    file = re.compile("\s*file-level\s*:\s*(?P<filename>[^,\s]*)").search(
        missing_information
    )
    page = re.compile("\s*page-level\s*:\s*(?P<pagenumber>[^,\s]*)").search(
        missing_information
    )
    order = re.compile("\s*order-level\s*:\s*(?P<order>[^,\s]*)").search(
        missing_information
    )
    base = re.compile("\s*base-level\s*:\s*(?P<base>.*)").search(missing_information)
    complete = re.compile("\(incomplete\)").search(missing_information)
    file_information = file.group("filename") if file else "Unknown"
    page_information = convert_num(page.group("pagenumber")) if page else "Unknown"
    order_information = (
        (
            convert_num(order.group("order")),
            (
                True
                if order.group("order") == "missing"
                or type(convert_num(order.group("order"))) in [int, str]
                else False
            ),
        )
        if order
        else "Unknown"
    )
    action_information = (base.group("base"), True) if base else ("Unknow", False)
    complete = ("non_complete", True) if complete else (None, False)
    return (
        file_information,
        page_information,
        order_information,
        action_information,
        complete,
    )


class recorder:
    def __init__(self, missing_information):
        """file-level: K3R1M8F.pdf, page-level: 5, order-level: 1, base-level: add a new text with rotation of 270 degrees and font size 12.(incomplete)"""
        self.file, self.page, self.order, self.action, self.complete = (
            missing_structure(missing_information)
        )
        self.doc = open(self.file)
        self.page, self.page_index = page_track(self.doc, self.page)
        self.rect, self.rect_index = rect_track(
            self.doc,
            extrracted_anno(self.doc.fileblock["filepath"], self.page, self.order),
        )
        self.recorder_block = {
            "operation": "instantiate_recorder",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
                ("action", self.action),
                ("complete", self.complete),
            ],
            "necessary_arguments": ["doc", "page", "clip", "action", "complete"],
            "transfered_arguments": [],
            "first_defined_arguments": ["doc", "page", "clip", "action", "complete"],
            "vaguly_defined_arguments": [],
            "tool_callings": [],
        }
        self.recorder_block = class_track(self.doc, self.recorder_block, "recorder")

    def recording(self):
        tool_calling_update("record", self.recorder_block)


def move_check(move):
    if type(move) == list and len(move) == 3:
        value_check = [True if type(x) in [int, float] else False for x in move[:2]]
        value_check.append(True if type(move[2]) == extrracted_anno else False)
    else:
        value_check = [False]
    if value_check[-1]:
        move[2] = (
            str(move[2].doc[0])
            + "-"
            + str(move[2].page[0])
            + "-"
            + str(move[2].order_or_annocolor[0])
        )
    return (move, True if all(value_check) else False)


def rotate_check(rotate):
    if type(rotate) == list and len(rotate) == 3:
        value_check = [True] if rotate[0] == "r" else [False]
        value_check.append(True if type(rotate[1]) in [int, float] else False)
        value_check.append(True if type(rotate[2]) == extrracted_anno else False)
    else:
        value_check = [False]
    if value_check[-1]:
        rotate[2] = (
            str(rotate[2].doc[0])
            + "-"
            + str(rotate[2].page[0])
            + "-"
            + str(rotate[2].order_or_annocolor[0])
        )
    return (rotate, True if all(value_check) else False)


def scal_check(scal):
    if type(scal) == list and len(scal) == 3:
        value_check = [True] if scal[0] == "sc" else [False]
        value_check.append(
            True if type(scal[1]) is list and len(scal[1]) == 2 else False
        )
        value_check.append(True if type(scal[2]) == extrracted_anno else False)
    else:
        value_check = [False]
    if value_check[-1]:
        scal[2] = (
            str(scal[2].doc[0])
            + "-"
            + str(scal[2].page[0])
            + "-"
            + str(scal[2].order_or_annocolor[0])
        )
    return (scal, True if all(value_check) else False)


class project_basic(basic):
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
        clip: any = "Unknown",
        move=None,
        rotation=None,
        scal=None,
    ):
        super().__init__(
            doc,
            pagenumber,
        )
        self.rect, self.rect_index = rect_track(self.doc, clip)
        self.move = (move, move_check(move))
        self.rotation = (rotation, rotate_check(rotation))
        self.scal = (scal, scal_check(scal))
        self.project_block = {
            "operation": "instantiate_projector",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
                ("move", self.move),
                ("rotation", self.rotation),
                ("scal", self.scal),
            ],
            "necessary_arguments": [
                "doc",
                "page",
                "clip",
                ["move", "rotation", "scal"],
            ],
            "transfered_arguments": ["doc", "page", "clip"],
            "first_defined_arguments": ["move", "rotation", "scal"],
            "vaguly_defined_arguments": ["move", "rotation", "scal"],
            "tool_callings": [],
        }

    def project(self):
        tool_calling_update("project", self.project_block)
        return self.doc


class Projector(project_basic):
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
        clip: any = "Unknown",
        move=None,
        rotation=None,
        scal=None,
    ):
        super().__init__(doc, pagenumber, clip, move, rotation, scal)
        self.project_block = class_track(self.doc, self.project_block, "change_maker")


class project_draw(project_basic):
    def __init__(
        self,
        doc: any = "Unknown",
        pagenumber: any = "Unknown",
        clip: any = "Unknown",
        sel_drawings=None,
        cdrawings=None,
        move=None,
        rotation=None,
        scal=None,
    ):
        super().__init__(doc, pagenumber, clip, move, rotation, scal)
        self.sel_drawings = drawing_list_check(sel_drawings)
        self.cdrawings = drawing_list_check(cdrawings)
        self.project_block = {
            "operation": "instantiate_draw_projector",
            "arguments_value": [
                ("doc", self.doc.fileblock["filepath"]),
                ("page", self.page),
                ("clip", self.rect),
                ("move", self.move),
                ("rotation", self.rotation),
                ("scal", self.scal),
                ("sel_drawings", self.sel_drawings),
                ("cdrawings", self.cdrawings),
            ],
            "necessary_arguments": [
                "doc",
                "page",
                "clip",
                ["move", "rotation", "scal"],
                "sel_drawings",
                "cdrawings",
            ],
            "transfered_arguments": [
                "doc",
                "page",
                "clip",
                "sel_drawings",
                "cdrawings",
            ],
            "first_defined_arguments": ["move", "rotation", "scal"],
            "vaguly_defined_arguments": ["move", "rotation", "scal"],
            "tool_callings": [],
        }
        self.project_block = class_track(self.doc, self.project_block, "change_maker")
