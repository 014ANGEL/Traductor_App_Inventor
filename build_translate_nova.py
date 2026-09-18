# -*- coding: utf-8 -*-
"""Build a real MIT App Inventor project: TraductorGlobal.aia"""
from __future__ import annotations

import json
import struct
import zlib
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent / "TraductorGlobal.aia"
SRC_DIR = "src/appinventor/ai_user/TraductorGlobal"

NAVY = "&HFF102A44"
NAVY_DEEP = "&HFF081526"
NAVY_MID = "&HFF1A4060"
TEAL = "&HFF12B39A"
TEAL_DARK = "&HFF0B746C"
TEAL_SOFT = "&HFFD7F4EE"
BG = "&HFFE6EEF3"
WHITE = "&HFFFFFFFF"
TEXT = "&HFF0F172A"
MUTED = "&HFF5B6B7C"
MINT = "&HFFE6F8F4"
CREAM = "&HFFFFF3E4"
SOFT = "&HFFF4F8FB"
LINE = "&HFFD3DEE6"
SHADOW = "&HFFC5D2DC"
SHADOW_NAVY = "&HFF06101C"
WELL = "&HFFD7E2EA"
GOLD = "&HFFD97706"
CREAM_LIP = "&HFFE8C9A0"
RED = "&HFFDC2626"
RED_SOFT = "&HFFFEF2F2"

FILL = "-2"
AUTO = "-1"

_id = 0
_uuid = 1000


def nid() -> str:
    global _id
    _id += 1
    return f"tn{_id}"


def uuid() -> str:
    global _uuid
    _uuid += 1
    return str(_uuid)


def esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def field(name: str, value) -> str:
    return f'<field name="{name}">{esc(value)}</field>'


def mut(**attrs) -> str:
    parts = " ".join(f'{k}="{v}"' for k, v in attrs.items() if v is not None)
    return f"<mutation {parts}></mutation>"


def block(typ: str, inner: str, x=None, y=None) -> str:
    attrs = f'type="{typ}" id="{nid()}"'
    if x is not None:
        attrs += f' x="{x}" y="{y}"'
    return f"<block {attrs}>{inner}</block>"


def value(name: str, inner: str) -> str:
    return f'<value name="{name}">{inner}</value>'


def statement(name: str, inner: str) -> str:
    return f'<statement name="{name}">{inner}</statement>'


def comment(text: str, pinned: str = "false", h: int = 48, w: int = 220) -> str:
    return f'<comment pinned="{pinned}" h="{h}" w="{w}">{esc(text)}</comment>'


def chain(*stmts: str) -> str:
    stmts = [s for s in stmts if s]
    if not stmts:
        return ""
    acc = stmts[-1]
    for s in reversed(stmts[:-1]):
        if not s.endswith("</block>"):
            raise ValueError("chain item does not end with </block>")
        acc = s[:-8] + f"<next>{acc}</next></block>"
    return acc


def text(s: str) -> str:
    return block("text", field("TEXT", s))


def num(n) -> str:
    return block("math_number", field("NUM", str(n)))


def boolean(v: bool) -> str:
    return block("logic_boolean", field("BOOL", "TRUE" if v else "FALSE"))


def text_length(v: str) -> str:
    return block("text_length", value("VALUE", v))


def color_rgb(r: int, g: int, b: int) -> str:
    return block("color_make_color", value("COLORLIST", make_list(num(r), num(g), num(b))))


def gget(name: str) -> str:
    return block("lexical_variable_get", field("VAR", f"global {name}"))


def lget(name: str) -> str:
    return block("lexical_variable_get", field("VAR", name))


def gset(name: str, val: str) -> str:
    return block("lexical_variable_set", field("VAR", f"global {name}") + value("VALUE", val))


def eq(a: str, b: str) -> str:
    return block("logic_compare", field("OP", "EQ") + value("A", a) + value("B", b))


def neq(a: str, b: str) -> str:
    return block("logic_compare", field("OP", "NEQ") + value("A", a) + value("B", b))


def gt(a: str, b: str) -> str:
    return block("math_compare", field("OP", "GT") + value("A", a) + value("B", b))


def land(a: str, b: str) -> str:
    return block("logic_operation", field("OP", "AND") + value("A", a) + value("B", b))


def lnot(a: str) -> str:
    return block("logic_negate", value("BOOL", a))


def empty_text(v: str) -> str:
    return block("text_isEmpty", value("VALUE", v))


def trim(v: str) -> str:
    return block("text_trim", value("TEXT", v))


def join(*parts: str) -> str:
    inner = mut(items=str(len(parts))) + "".join(
        value(f"ADD{i}", p) for i, p in enumerate(parts)
    )
    return block("text_join", inner)


def make_list(*items: str) -> str:
    inner = mut(items=str(len(items)))
    if items:
        inner += "".join(value(f"ADD{i}", it) for i, it in enumerate(items))
    return block("lists_create_with", inner)


def empty_list() -> str:
    return block("lists_create_with", mut(items="0"))


def select_item(lst: str, index: str) -> str:
    return block("lists_select_item", value("LIST", lst) + value("NUM", index))


def list_length(lst: str) -> str:
    return block("lists_length", value("LIST", lst))


def list_empty(lst: str) -> str:
    return block("lists_is_empty", value("LIST", lst))


def lookup_pairs(key: str, lst: str, missing: str) -> str:
    return block(
        "lists_lookup_in_pairs",
        value("KEY", key) + value("LIST", lst) + value("NOTFOUND", missing),
    )


def position_in(item: str, lst: str) -> str:
    return block("lists_position_in", value("ITEM", item) + value("LIST", lst))


def insert_item(lst: str, index: str, item: str) -> str:
    return block(
        "lists_insert_item",
        value("LIST", lst) + value("INDEX", index) + value("ITEM", item),
    )


def remove_item(lst: str, index: str) -> str:
    return block("lists_remove_item", value("LIST", lst) + value("INDEX", index))


def add_item(lst: str, item: str) -> str:
    return block(
        "lists_add_items",
        mut(items="1") + value("LIST", lst) + value("ITEM0", item),
    )


def foreach(var: str, lst: str, body: str) -> str:
    return block(
        "controls_forEach",
        field("VAR", var) + value("LIST", lst) + statement("DO", body),
    )


def randint(a: str, b: str) -> str:
    return block("math_random_int", value("FROM", a) + value("TO", b))


def iff(cond: str, then: str, els: str | None = None) -> str:
    inner = ""
    if els is not None:
        inner += mut(**{"else": "1"})
    inner += value("IF0", cond) + statement("DO0", then)
    if els is not None:
        inner += statement("ELSE", els)
    return block("controls_if", inner)


def getp(ctype: str, inst: str, prop: str) -> str:
    return block(
        "component_set_get",
        mut(
            component_type=ctype,
            set_or_get="get",
            property_name=prop,
            is_generic="false",
            instance_name=inst,
        )
        + field("COMPONENT_SELECTOR", inst)
        + field("PROP", prop),
    )


def setp(ctype: str, inst: str, prop: str, val: str) -> str:
    return block(
        "component_set_get",
        mut(
            component_type=ctype,
            set_or_get="set",
            property_name=prop,
            is_generic="false",
            instance_name=inst,
        )
        + field("COMPONENT_SELECTOR", inst)
        + field("PROP", prop)
        + value("VALUE", val),
    )


def call(ctype: str, inst: str, method: str, *args: str) -> str:
    inner = mut(
        component_type=ctype,
        method_name=method,
        is_generic="false",
        instance_name=inst,
    ) + field("COMPONENT_SELECTOR", inst)
    for i, a in enumerate(args):
        inner += value(f"ARG{i}", a)
    return block("component_method", inner)


def event(ctype: str, inst: str, ev: str, body: str, x: int, y: int, note: str | None = None) -> str:
    inner = mut(
        component_type=ctype,
        is_generic="false",
        instance_name=inst,
        event_name=ev,
    ) + field("COMPONENT_SELECTOR", inst)
    if note:
        inner += comment(note)
    inner += statement("DO", body)
    return block("component_event", inner, x=x, y=y)


def proc_def(name: str, body: str, x: int, y: int, args: list[str] | None = None, note: str | None = None) -> str:
    inner = ""
    if args:
        inner += "<mutation>" + "".join(f'<arg name="{a}"></arg>' for a in args) + "</mutation>"
    inner += field("NAME", name)
    if args:
        for i, a in enumerate(args):
            inner += field(f"VAR{i}", a)
    if note:
        inner += comment(note)
    inner += statement("STACK", body)
    return block("procedures_defnoreturn", inner, x=x, y=y)


def proc_call(name: str, args: list[tuple[str, str]] | None = None) -> str:
    if args:
        inner = f'<mutation name="{name}">' + "".join(f'<arg name="{a}"></arg>' for a, _ in args) + "</mutation>"
    else:
        inner = f'<mutation name="{name}"></mutation>'
    inner += field("PROCNAME", name)
    if args:
        for i, (_, val) in enumerate(args):
            inner += value(f"ARG{i}", val)
    return block("procedures_callnoreturn", inner)


def global_decl(name: str, val: str, x: int, y: int, note: str | None = None) -> str:
    inner = field("NAME", name)
    if note:
        inner += comment(note)
    inner += value("VALUE", val)
    return block("global_declaration", inner, x=x, y=y)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def C(typ: str, name: str, version: str, **props):
    node = {"$Name": name, "$Type": typ, "$Version": version, "Uuid": uuid()}
    node.update(props)
    return node


def label(name: str, text_v: str, **props):
    d = {
        "HasMargins": "False",
        "Text": text_v,
        "TextColor": TEXT,
    }
    d.update(props)
    return C("Label", name, "5", **d)


def button(name: str, text_v: str, **props):
    d = {
        "Shape": "1",
        "Text": text_v,
        "FontBold": "True",
        "TextColor": WHITE,
        "BackgroundColor": TEAL,
        "Height": "48",
    }
    d.update(props)
    return C("Button", name, "7", **d)


def spacer(name: str, h: str = "10"):
    return C("Label", name, "5", HasMargins="False", Height=h, Width=FILL, Text="")


def card(name: str, color: str, children: list, **props):
    d = {
        "Width": FILL,
        "AlignHorizontal": "3",
        "BackgroundColor": color,
        "$Components": children,
    }
    d.update(props)
    return C("VerticalArrangement", name, "4", **d)


def ha(name: str, children: list, **props):
    d = {"Width": FILL, "AlignVertical": "2", "$Components": children}
    d.update(props)
    return C("HorizontalArrangement", name, "4", **d)


def va(name: str, children: list, **props):
    d = {"$Components": children}
    d.update(props)
    return C("VerticalArrangement", name, "4", **d)


def gap(name: str, w: str = "8"):
    return C("Label", name, "5", HasMargins="False", Width=w, Height="1", Text="")


def vbar(name: str, color: str, w: str = "7"):
    return C(
        "Label",
        name,
        "5",
        HasMargins="False",
        Width=w,
        Height=FILL,
        BackgroundColor=color,
        Text="",
    )


def hbar(name: str, color: str, h: str = "5"):
    return C(
        "Label",
        name,
        "5",
        HasMargins="False",
        Height=h,
        Width=FILL,
        BackgroundColor=color,
        Text="",
    )


def raised_card(name: str, color: str, children: list, accent=None, shadow=None, **props):
    if shadow is None:
        shadow = SHADOW
    face = card(f"{name}Cara", color, children, Width=FILL)
    if accent:
        face = ha(
            f"{name}Cuerpo",
            [vbar(f"{name}Acento", accent, "7"), face],
            Width=FILL,
            AlignVertical="1",
            BackgroundColor=color,
        )
    d = {
        "Width": FILL,
        "BackgroundColor": shadow,
        "$Components": [face, hbar(f"{name}Sombra", shadow, "5")],
    }
    d.update(props)
    return C("VerticalArrangement", name, "4", **d)


def inset_well(name: str, child):
    return card(
        name,
        WELL,
        [
            spacer(f"{name}T", "5"),
            ha(
                f"{name}Fila",
                [gap(f"{name}L", "5"), child, gap(f"{name}R", "5")],
                Width=FILL,
                AlignVertical="1",
            ),
            spacer(f"{name}B", "5"),
        ],
        Width=FILL,
    )


def raised_action(name: str, btn, lip_color: str):
    return va(
        name,
        [btn, hbar(f"{name}Lip", lip_color, "5")],
        Width=FILL,
        BackgroundColor=lip_color,
    )


def color_error() -> str:
    return color_rgb(220, 38, 38)


def color_ok() -> str:
    return color_rgb(15, 118, 110)


def color_muted() -> str:
    return color_rgb(100, 116, 139)


def color_teal() -> str:
    return color_rgb(18, 179, 154)


def color_teal_dark() -> str:
    return color_rgb(11, 116, 108)


HINT_ESTADO = "Elige idiomas, escribe y pulsa Traducir."


def build_scm() -> str:
    screen = {
        "authURL": ["ai2.appinventor.mit.edu"],
        "YaVersion": "232",
        "Source": "Form",
        "Properties": {
            "$Name": "Screen1",
            "$Type": "Form",
            "$Version": "31",
            "AppName": "Traductor global",
            "Title": "Traductor global",
            "AboutScreen": "Traductor global traduce entre 8 idiomas con voz, historial y una frase del día. Toca un recorte reciente para restaurarlo. Mantén pulsada la traducción para copiarla.",
            "AccentColor": TEAL,
            "ActionBar": "False",
            "AlignHorizontal": "3",
            "BackgroundColor": BG,
            "Icon": "icon.png",
            "PrimaryColor": NAVY,
            "PrimaryColorDark": NAVY_DEEP,
            "ScreenOrientation": "portrait",
            "Scrollable": "True",
            "ShowListsAsJson": "True",
            "ShowStatusBar": "True",
            "Theme": "AppTheme.Light",
            "TitleVisible": "False",
            "Uuid": "0",
            "$Components": [
                card(
                    "vaPantalla",
                    BG,
                    [
                        card(
                            "vaEncabezado",
                            NAVY_DEEP,
                            [
                                hbar("barraTecho", TEAL, "4"),
                                card(
                                    "vaHero",
                                    NAVY,
                                    [
                                        spacer("spTop", "18"),
                                        ha(
                                            "haLogo",
                                            [
                                                C("Label", "spLogoL", "5", HasMargins="False", Width=FILL, Text=""),
                                                card(
                                                    "vaMarcoLogo",
                                                    WHITE,
                                                    [
                                                        spacer("spMarco1", "5"),
                                                        ha(
                                                            "haMarcoIn",
                                                            [
                                                                gap("spMarcoL", "5"),
                                                                card(
                                                                    "vaFondoLogo",
                                                                    TEAL,
                                                                    [
                                                                        spacer("spLogoIn1", "6"),
                                                                        ha(
                                                                            "haLogoImg",
                                                                            [
                                                                                gap("spImgL", "6"),
                                                                                C(
                                                                                    "Image",
                                                                                    "imgLogo",
                                                                                    "6",
                                                                                    Picture="icon.png",
                                                                                    Width="48",
                                                                                    Height="48",
                                                                                    ScalePictureToFit="True",
                                                                                ),
                                                                                gap("spImgR", "6"),
                                                                            ],
                                                                        ),
                                                                        spacer("spLogoIn2", "6"),
                                                                    ],
                                                                    Width="60",
                                                                    AlignHorizontal="3",
                                                                ),
                                                                gap("spMarcoR", "5"),
                                                            ],
                                                        ),
                                                        spacer("spMarco2", "5"),
                                                    ],
                                                    Width="70",
                                                    AlignHorizontal="3",
                                                ),
                                                C("Label", "spLogoR", "5", HasMargins="False", Width=FILL, Text=""),
                                            ],
                                            AlignVertical="2",
                                        ),
                                        spacer("spLogo", "10"),
                                        label(
                                            "lblTitulo",
                                            "Traductor global",
                                            FontBold="True",
                                            FontSize="26",
                                            TextAlignment="1",
                                            TextColor=WHITE,
                                            Width=FILL,
                                        ),
                                        label(
                                            "lblSubtitulo",
                                            "Traduce claro, rápido y en tu idioma.",
                                            FontSize="13",
                                            TextAlignment="1",
                                            TextColor="&HFFB7C9D6",
                                            Width=FILL,
                                        ),
                                        spacer("spChip0", "14"),
                                        ha(
                                            "haChipWrap",
                                            [
                                                gap("spChipL", "28"),
                                                ha(
                                                    "vaChipPar",
                                                    [
                                                        vbar("barraChipL", TEAL, "6"),
                                                        card(
                                                            "vaChipTexto",
                                                            NAVY_MID,
                                                            [
                                                                spacer("spChip1", "9"),
                                                                label(
                                                                    "lblParIdiomas",
                                                                    "Español  →  English",
                                                                    FontBold="True",
                                                                    FontSize="13",
                                                                    TextAlignment="1",
                                                                    TextColor=WHITE,
                                                                    Width=FILL,
                                                                ),
                                                                spacer("spChip2", "9"),
                                                            ],
                                                            Width=FILL,
                                                        ),
                                                        vbar("barraChipR", TEAL, "6"),
                                                    ],
                                                    Width=FILL,
                                                    AlignVertical="1",
                                                    BackgroundColor=NAVY_MID,
                                                ),
                                                gap("spChipR", "28"),
                                            ],
                                        ),
                                        spacer("spHead", "18"),
                                        ha(
                                            "haTarjetaFlotante",
                                            [
                                                gap("spFloatL", "14"),
                                                raised_card(
                                                    "vaTarjetaIdiomas",
                                                    WHITE,
                                                    [
                                                        spacer("spId0", "14"),
                                                        ha(
                                                            "haIdiomas",
                                                            [
                                                                va(
                                                                    "vaOrigen",
                                                                    [
                                                                        label(
                                                                            "lblEtiquetaOrigen",
                                                                            "DE",
                                                                            FontBold="True",
                                                                            FontSize="11",
                                                                            TextColor=MUTED,
                                                                            Width=FILL,
                                                                        ),
                                                                        C(
                                                                            "Spinner",
                                                                            "spnOrigen",
                                                                            "1",
                                                                            Width=FILL,
                                                                            Prompt="Idioma de origen",
                                                                            ElementsFromString="Español,English,Français,Português,Deutsch,中文,हिन्दी,العربية",
                                                                            Selection="Español",
                                                                        ),
                                                                        label(
                                                                            "lblCodigoOrigen",
                                                                            "es",
                                                                            FontBold="True",
                                                                            FontSize="11",
                                                                            TextColor=TEAL_DARK,
                                                                            Width=FILL,
                                                                        ),
                                                                    ],
                                                                    Width=FILL,
                                                                ),
                                                                va(
                                                                    "vaCentroSwap",
                                                                    [
                                                                        spacer("spSwap", "12"),
                                                                        card(
                                                                            "vaAnilloSwap",
                                                                            TEAL,
                                                                            [
                                                                                spacer("spAnillo1", "4"),
                                                                                ha(
                                                                                    "haAnillo",
                                                                                    [
                                                                                        gap("spAnilloL", "4"),
                                                                                        button(
                                                                                            "btnIntercambiar",
                                                                                            "⇄",
                                                                                            FontBold="True",
                                                                                            FontSize="18",
                                                                                            Width="48",
                                                                                            Height="48",
                                                                                            Shape="3",
                                                                                            BackgroundColor=NAVY,
                                                                                        ),
                                                                                        gap("spAnilloR", "4"),
                                                                                    ],
                                                                                ),
                                                                                spacer("spAnillo2", "4"),
                                                                            ],
                                                                            Width="56",
                                                                            AlignHorizontal="3",
                                                                        ),
                                                                    ],
                                                                    AlignHorizontal="3",
                                                                    Width="64",
                                                                ),
                                                                va(
                                                                    "vaDestino",
                                                                    [
                                                                        label(
                                                                            "lblEtiquetaDestino",
                                                                            "A",
                                                                            FontBold="True",
                                                                            FontSize="11",
                                                                            TextColor=MUTED,
                                                                            Width=FILL,
                                                                        ),
                                                                        C(
                                                                            "Spinner",
                                                                            "spnDestino",
                                                                            "1",
                                                                            Width=FILL,
                                                                            Prompt="Idioma de destino",
                                                                            ElementsFromString="Español,English,Français,Português,Deutsch,中文,हिन्दी,العربية",
                                                                            Selection="English",
                                                                        ),
                                                                        label(
                                                                            "lblCodigoDestino",
                                                                            "en",
                                                                            FontBold="True",
                                                                            FontSize="11",
                                                                            TextColor=TEAL_DARK,
                                                                            Width=FILL,
                                                                        ),
                                                                    ],
                                                                    Width=FILL,
                                                                ),
                                                            ],
                                                        ),
                                                        spacer("spId1", "14"),
                                                    ],
                                                    accent=TEAL,
                                                    shadow=SHADOW_NAVY,
                                                ),
                                                gap("spFloatR", "14"),
                                            ],
                                        ),
                                        spacer("spHead2", "6"),
                                    ],
                                    AlignHorizontal="3",
                                    Width=FILL,
                                ),
                                hbar("barraAcento", TEAL, "6"),
                                hbar("barraAcentoSombra", TEAL_DARK, "3"),
                            ],
                            AlignHorizontal="3",
                            Width=FILL,
                        ),
                        ha(
                            "haCuerpo",
                            [
                                gap("spIzq", "14"),
                                va(
                                    "vaContenido",
                                    [
                                        spacer("sp1", "14"),
                                        raised_card(
                                            "vaTarjetaEntrada",
                                            WHITE,
                                            [
                                                spacer("spIn0", "14"),
                                                ha(
                                                    "haEntradaTitulo",
                                                    [
                                                        label(
                                                            "lblEtiquetaEntrada",
                                                            "Texto a traducir",
                                                            FontBold="True",
                                                            FontSize="13",
                                                            TextColor=NAVY,
                                                            Width=FILL,
                                                        ),
                                                        label(
                                                            "lblContador",
                                                            "0",
                                                            FontSize="11",
                                                            TextAlignment="2",
                                                            TextColor=MUTED,
                                                            Width="72",
                                                        ),
                                                    ],
                                                ),
                                                spacer("spInHint", "8"),
                                                inset_well(
                                                    "vaPozoEntrada",
                                                    C(
                                                        "TextBox",
                                                        "txtEntrada",
                                                        "14",
                                                        BackgroundColor=WHITE,
                                                        FontSize="17",
                                                        Height="108",
                                                        Width=FILL,
                                                        Hint="Escribe o dicta lo que quieres traducir",
                                                        MultiLine="True",
                                                        TextColor=TEXT,
                                                    ),
                                                ),
                                                spacer("spIn1", "10"),
                                                ha(
                                                    "haEntradaAcciones",
                                                    [
                                                        raised_action(
                                                            "vaBtnHablar",
                                                            button(
                                                                "btnHablar",
                                                                "🎤  Dictar",
                                                                Width=FILL,
                                                                Height="48",
                                                                BackgroundColor=NAVY,
                                                                FontSize="14",
                                                            ),
                                                            NAVY_DEEP,
                                                        ),
                                                        gap("spBtnIn", "8"),
                                                        raised_action(
                                                            "vaBtnLimpiar",
                                                            button(
                                                                "btnLimpiar",
                                                                "Limpiar",
                                                                Width=FILL,
                                                                Height="48",
                                                                BackgroundColor=WHITE,
                                                                TextColor=NAVY,
                                                                FontSize="14",
                                                            ),
                                                            LINE,
                                                        ),
                                                    ],
                                                ),
                                                spacer("spIn2", "14"),
                                            ],
                                            accent=NAVY,
                                        ),
                                        spacer("sp3", "14"),
                                        raised_action(
                                            "vaBtnTraducir",
                                            button(
                                                "btnTraducir",
                                                "Traducir",
                                                Width=FILL,
                                                Height="54",
                                                FontSize="18",
                                                BackgroundColor=TEAL,
                                                Shape="1",
                                            ),
                                            TEAL_DARK,
                                        ),
                                        spacer("sp4", "10"),
                                        card(
                                            "vaEstado",
                                            TEAL_SOFT,
                                            [
                                                spacer("spEst0", "8"),
                                                label(
                                                    "lblEstado",
                                                    HINT_ESTADO,
                                                    FontSize="12",
                                                    TextAlignment="1",
                                                    TextColor=MUTED,
                                                    Width=FILL,
                                                ),
                                                spacer("spEst1", "8"),
                                            ],
                                            Width=FILL,
                                        ),
                                        spacer("sp5", "14"),
                                        raised_card(
                                            "vaTarjetaResultado",
                                            MINT,
                                            [
                                                spacer("spOut0", "14"),
                                                label(
                                                    "lblEtiquetaResultado",
                                                    "Traducción",
                                                    FontBold="True",
                                                    FontSize="13",
                                                    TextColor=NAVY,
                                                    Width=FILL,
                                                ),
                                                spacer("spOutHint", "8"),
                                                inset_well(
                                                    "vaPozoResultado",
                                                    C(
                                                        "TextBox",
                                                        "txtTraduccion",
                                                        "14",
                                                        BackgroundColor=WHITE,
                                                        Enabled="True",
                                                        FontSize="18",
                                                        Height="96",
                                                        Width=FILL,
                                                        Hint="Aquí verás el resultado",
                                                        MultiLine="True",
                                                        ReadOnly="True",
                                                        TextColor=TEXT,
                                                    ),
                                                ),
                                                label(
                                                    "lblAyudaCopia",
                                                    "Mantén pulsado el texto para copiarlo.",
                                                    FontSize="11",
                                                    TextColor=MUTED,
                                                    Width=FILL,
                                                ),
                                                spacer("spOut1", "10"),
                                                ha(
                                                    "haResultadoAcciones",
                                                    [
                                                        raised_action(
                                                            "vaBtnEscuchar",
                                                            button(
                                                                "btnEscuchar",
                                                                "🔊  Escuchar",
                                                                Width=FILL,
                                                                Height="48",
                                                                BackgroundColor=NAVY,
                                                                FontSize="14",
                                                            ),
                                                            NAVY_DEEP,
                                                        ),
                                                        gap("spBtnOut", "8"),
                                                        raised_action(
                                                            "vaBtnCopiar",
                                                            button(
                                                                "btnCopiar",
                                                                "📤  Compartir",
                                                                Width=FILL,
                                                                Height="48",
                                                                BackgroundColor=NAVY,
                                                                FontSize="14",
                                                            ),
                                                            NAVY_DEEP,
                                                        ),
                                                    ],
                                                ),
                                                spacer("spOut2", "14"),
                                            ],
                                            accent=TEAL,
                                        ),
                                        spacer("sp6", "14"),
                                        raised_card(
                                            "vaTarjetaFrase",
                                            CREAM,
                                            [
                                                spacer("spFr0", "14"),
                                                ha(
                                                    "haFraseTitulo",
                                                    [
                                                        label(
                                                            "lblEtiquetaFrase",
                                                            "✨  Frase del día",
                                                            FontBold="True",
                                                            FontSize="13",
                                                            TextColor=NAVY,
                                                            Width=FILL,
                                                        ),
                                                        button(
                                                            "btnOtraFrase",
                                                            "Otra",
                                                            FontBold="True",
                                                            FontSize="12",
                                                            Height="36",
                                                            Width="72",
                                                            BackgroundColor=WHITE,
                                                            TextColor=NAVY,
                                                        ),
                                                    ],
                                                ),
                                                spacer("spFrTxt", "8"),
                                                card(
                                                    "vaCitaFrase",
                                                    WHITE,
                                                    [
                                                        spacer("spCita0", "10"),
                                                        ha(
                                                            "haCita",
                                                            [
                                                                gap("spCitaL", "10"),
                                                                label(
                                                                    "lblFrase",
                                                                    '"Hello"\n\nEn Español:\n"Hola"',
                                                                    FontSize="16",
                                                                    TextColor=TEXT,
                                                                    Width=FILL,
                                                                ),
                                                                gap("spCitaR", "10"),
                                                            ],
                                                        ),
                                                        spacer("spCita1", "10"),
                                                    ],
                                                    Width=FILL,
                                                ),
                                                spacer("spFr1", "10"),
                                                raised_action(
                                                    "vaBtnUsarFrase",
                                                    button(
                                                        "btnUsarFrase",
                                                        "Usar esta frase",
                                                        Width=FILL,
                                                        Height="44",
                                                        BackgroundColor=WHITE,
                                                        TextColor=NAVY,
                                                        FontSize="14",
                                                    ),
                                                    CREAM_LIP,
                                                ),
                                                spacer("spFr2", "14"),
                                            ],
                                            accent=GOLD,
                                        ),
                                        spacer("sp7", "14"),
                                        raised_card(
                                            "vaTarjetaHistorial",
                                            WHITE,
                                            [
                                                spacer("spHi0", "14"),
                                                ha(
                                                    "haHistorialTitulo",
                                                    [
                                                        label(
                                                            "lblEtiquetaHistorial",
                                                            "Recientes",
                                                            FontBold="True",
                                                            FontSize="15",
                                                            TextColor=NAVY,
                                                            Width=FILL,
                                                        ),
                                                        button(
                                                            "btnBorrarHistorial",
                                                            "Vaciar",
                                                            FontBold="False",
                                                            FontSize="12",
                                                            Height="36",
                                                            Width="78",
                                                            BackgroundColor=RED_SOFT,
                                                            TextColor=RED,
                                                            Shape="1",
                                                            Visible="False",
                                                        ),
                                                    ],
                                                ),
                                                label(
                                                    "lblAyudaHistorial",
                                                    "Toca una traducción para volver a ella.",
                                                    FontSize="11",
                                                    TextColor=MUTED,
                                                    Width=FILL,
                                                    Visible="False",
                                                ),
                                                spacer("spHiEmpty", "8"),
                                                label(
                                                    "lblSinRecientes",
                                                    "Todavía no hay traducciones.\nCuando traduzcas, aparecerán aquí.",
                                                    FontSize="13",
                                                    TextAlignment="1",
                                                    TextColor=MUTED,
                                                    Width=FILL,
                                                ),
                                                C(
                                                    "ListView",
                                                    "lstRecientes",
                                                    "6",
                                                    BackgroundColor=SOFT,
                                                    Height="168",
                                                    Width=FILL,
                                                    TextColor=TEXT,
                                                    TextSize="15",
                                                    Visible="False",
                                                ),
                                                spacer("spHi1", "14"),
                                            ],
                                            accent=NAVY,
                                        ),
                                        spacer("sp8", "12"),
                                        card(
                                            "vaPie",
                                            SOFT,
                                            [
                                                spacer("spPie0", "8"),
                                                label(
                                                    "lblPie",
                                                    "8 idiomas  ·  voz  ·  historial guardado",
                                                    FontSize="11",
                                                    TextAlignment="1",
                                                    TextColor=MUTED,
                                                    Width=FILL,
                                                ),
                                                spacer("spPie1", "8"),
                                            ],
                                            Width=FILL,
                                        ),
                                        spacer("sp9", "22"),
                                    ],
                                    Width=FILL,
                                ),
                                gap("spDer", "14"),
                            ],
                            AlignVertical="1",
                            Width=FILL,
                        ),
                    ],
                    Width=FILL,
                    AlignHorizontal="3",
                ),
                C("SpeechRecognizer", "ReconocimientoDeVoz", "2", UseLegacy="True", Language="es-ES"),
                C("TextToSpeech", "TextoAVoz", "5", Language="en", Country="USA"),
                C("Translator", "Traductor", "1"),
                C("TinyDB", "TinyDB1", "2"),
                C("Notifier", "Notifier1", "6"),
                C("Sharing", "Compartir", "1"),
                C(
                    "Clock",
                    "RelojEstado",
                    "4",
                    TimerAlwaysFires="False",
                    TimerEnabled="False",
                    TimerInterval="4000",
                ),
            ],
        },
    }
    payload = json.dumps(screen, ensure_ascii=False, separators=(",", ":"))
    return "#|\n$JSON\n" + payload + "\n|#"


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------

def pair(a: str, b: str) -> str:
    return make_list(text(a), text(b))


def phrase(*words: str) -> str:
    return make_list(*[text(w) for w in words])


def build_bky() -> str:
    blocks = []

    # VARIABLES
    blocks.append(global_decl("idiomaOrigen", text("Español"), 20, 20, "VARIABLES"))
    blocks.append(global_decl("idiomaDestino", text("English"), 20, 90))
    blocks.append(global_decl("textoEntrada", text(""), 20, 160))
    blocks.append(global_decl("textoTraducido", text(""), 20, 230))
    blocks.append(global_decl("historial", empty_list(), 20, 300))
    blocks.append(global_decl("fraseActual", empty_list(), 20, 370))
    blocks.append(global_decl("indiceFrase", num(1), 20, 440))
    blocks.append(global_decl("listaIdiomas", empty_list(), 20, 510))
    blocks.append(global_decl("paresCodigo", empty_list(), 20, 580))
    blocks.append(global_decl("paresVoz", empty_list(), 20, 650))
    blocks.append(global_decl("paresPais", empty_list(), 20, 720))
    blocks.append(global_decl("listaFrases", empty_list(), 20, 790))
    blocks.append(global_decl("vistaHistorial", empty_list(), 20, 860))
    blocks.append(global_decl("tempOrigen", num(1), 20, 930))
    blocks.append(global_decl("tempDestino", num(2), 20, 1000))
    blocks.append(global_decl("itemActual", empty_list(), 20, 1070))

    # IDIOMAS — preparar datos
    blocks.append(
        proc_def(
            "PrepararIdiomas",
            chain(
                gset(
                    "listaIdiomas",
                    make_list(
                        text("Español"),
                        text("English"),
                        text("Français"),
                        text("Português"),
                        text("Deutsch"),
                        text("中文"),
                        text("हिन्दी"),
                        text("العربية"),
                    ),
                ),
                gset(
                    "paresCodigo",
                    make_list(
                        pair("Español", "es"),
                        pair("English", "en"),
                        pair("Français", "fr"),
                        pair("Português", "pt"),
                        pair("Deutsch", "de"),
                        pair("中文", "zh"),
                        pair("हिन्दी", "hi"),
                        pair("العربية", "ar"),
                    ),
                ),
                gset(
                    "paresVoz",
                    make_list(
                        pair("Español", "es-ES"),
                        pair("English", "en-US"),
                        pair("Français", "fr-FR"),
                        pair("Português", "pt-BR"),
                        pair("Deutsch", "de-DE"),
                        pair("中文", "zh-CN"),
                        pair("हिन्दी", "hi-IN"),
                        pair("العربية", "ar-SA"),
                    ),
                ),
                gset(
                    "paresPais",
                    make_list(
                        pair("Español", "ESP"),
                        pair("English", "USA"),
                        pair("Français", "FRA"),
                        pair("Português", "BRA"),
                        pair("Deutsch", "DEU"),
                        pair("中文", "CHN"),
                        pair("हिन्दी", "IND"),
                        pair("العربية", "SAU"),
                    ),
                ),
                gset(
                    "listaFrases",
                    make_list(
                        phrase("Hola", "Hello", "Bonjour", "Olá", "Hallo", "你好", "नमस्ते", "مرحبا"),
                        phrase(
                            "Buenos días",
                            "Good morning",
                            "Bonjour",
                            "Bom dia",
                            "Guten Morgen",
                            "早上好",
                            "सुप्रभात",
                            "صباح الخير",
                        ),
                        phrase("Gracias", "Thank you", "Merci", "Obrigado", "Danke", "谢谢", "धन्यवाद", "شكرا"),
                        phrase(
                            "Hasta luego",
                            "See you later",
                            "À bientôt",
                            "Até logo",
                            "Bis später",
                            "再见",
                            "बाद में मिलते हैं",
                            "إلى اللقاء",
                        ),
                        phrase(
                            "¿Cómo estás?",
                            "How are you?",
                            "Comment ça va?",
                            "Como vai?",
                            "Wie geht's?",
                            "你好吗？",
                            "आप कैसे हैं?",
                            "كيف حالك؟",
                        ),
                        phrase(
                            "Bienvenido",
                            "Welcome",
                            "Bienvenue",
                            "Bem-vindo",
                            "Willkommen",
                            "欢迎",
                            "स्वागत है",
                            "أهلاً وسهلاً",
                        ),
                        phrase(
                            "Buenas noches",
                            "Good night",
                            "Bonne nuit",
                            "Boa noite",
                            "Gute Nacht",
                            "晚安",
                            "शुभ रात्रि",
                            "تصبح على خير",
                        ),
                        phrase(
                            "Te quiero",
                            "I love you",
                            "Je t'aime",
                            "Eu te amo",
                            "Ich liebe dich",
                            "我爱你",
                            "मैं तुमसे प्यार करता हूँ",
                            "أحبك",
                        ),
                    ),
                ),
            ),
            360,
            20,
            note="IDIOMAS",
        )
    )

    blocks.append(
        proc_def(
            "ActualizarIdiomas",
            chain(
                gset("idiomaOrigen", getp("Spinner", "spnOrigen", "Selection")),
                gset("idiomaDestino", getp("Spinner", "spnDestino", "Selection")),
                setp(
                    "Label",
                    "lblParIdiomas",
                    "Text",
                    join(gget("idiomaOrigen"), text("  →  "), gget("idiomaDestino")),
                ),
                setp(
                    "Label",
                    "lblCodigoOrigen",
                    "Text",
                    lookup_pairs(gget("idiomaOrigen"), gget("paresCodigo"), text("es")),
                ),
                setp(
                    "Label",
                    "lblCodigoDestino",
                    "Text",
                    lookup_pairs(gget("idiomaDestino"), gget("paresCodigo"), text("en")),
                ),
                proc_call("ConfigurarVoz"),
            ),
            360,
            420,
            note="IDIOMAS — Selección",
        )
    )

    blocks.append(
        proc_def(
            "ConfigurarVoz",
            chain(
                setp(
                    "SpeechRecognizer",
                    "ReconocimientoDeVoz",
                    "Language",
                    lookup_pairs(gget("idiomaOrigen"), gget("paresVoz"), text("es-ES")),
                ),
                setp(
                    "TextToSpeech",
                    "TextoAVoz",
                    "Language",
                    lookup_pairs(gget("idiomaDestino"), gget("paresCodigo"), text("en")),
                ),
                setp(
                    "TextToSpeech",
                    "TextoAVoz",
                    "Country",
                    lookup_pairs(gget("idiomaDestino"), gget("paresPais"), text("USA")),
                ),
            ),
            360,
            620,
            note="VOZ",
        )
    )

    blocks.append(
        proc_def(
            "IntercambiarIdiomas",
            chain(
                gset("tempOrigen", getp("Spinner", "spnOrigen", "SelectionIndex")),
                gset("tempDestino", getp("Spinner", "spnDestino", "SelectionIndex")),
                gset("textoEntrada", getp("TextBox", "txtEntrada", "Text")),
                gset("textoTraducido", getp("TextBox", "txtTraduccion", "Text")),
                setp("Spinner", "spnOrigen", "SelectionIndex", gget("tempDestino")),
                setp("Spinner", "spnDestino", "SelectionIndex", gget("tempOrigen")),
                setp("TextBox", "txtEntrada", "Text", gget("textoTraducido")),
                setp("TextBox", "txtTraduccion", "Text", gget("textoEntrada")),
                gset("textoEntrada", getp("TextBox", "txtEntrada", "Text")),
                gset("textoTraducido", getp("TextBox", "txtTraduccion", "Text")),
                proc_call("ActualizarIdiomas"),
                proc_call("MostrarFraseDelDia"),
                proc_call("ActualizarContador"),
            ),
            360,
            900,
            note="IDIOMAS — Intercambio",
        )
    )

    # TRADUCCIÓN
    blocks.append(
        proc_def(
            "TraducirTexto",
            chain(
                gset("textoEntrada", trim(getp("TextBox", "txtEntrada", "Text"))),
                setp("TextBox", "txtEntrada", "Text", gget("textoEntrada")),
                proc_call("ActualizarIdiomas"),
                iff(
                    empty_text(gget("textoEntrada")),
                    proc_call(
                        "MostrarAviso",
                        [("mensaje", text("Escribe o dicta un texto para traducir."))],
                    ),
                    iff(
                        eq(gget("idiomaOrigen"), gget("idiomaDestino")),
                        proc_call(
                            "MostrarAviso",
                            [("mensaje", text("Elige dos idiomas diferentes."))],
                        ),
                        chain(
                            setp("Button", "btnTraducir", "Enabled", boolean(False)),
                            setp("Button", "btnTraducir", "Text", text("Traduciendo...")),
                            setp("Button", "btnTraducir", "BackgroundColor", color_teal_dark()),
                            setp("Clock", "RelojEstado", "TimerEnabled", boolean(False)),
                            setp("Label", "lblEstado", "Text", text("Traduciendo tu texto...")),
                            setp("Label", "lblEstado", "TextColor", color_ok()),
                            call(
                                "Notifier",
                                "Notifier1",
                                "ShowProgressDialog",
                                text("Traduciendo tu texto"),
                                text("Traductor global"),
                            ),
                            call(
                                "Translator",
                                "Traductor",
                                "RequestTranslation",
                                join(
                                    lookup_pairs(gget("idiomaOrigen"), gget("paresCodigo"), text("es")),
                                    text("-"),
                                    lookup_pairs(gget("idiomaDestino"), gget("paresCodigo"), text("en")),
                                ),
                                gget("textoEntrada"),
                            ),
                        ),
                    ),
                ),
            ),
            760,
            20,
            note="TRADUCCIÓN",
        )
    )

    blocks.append(
        proc_def(
            "LimpiarCampos",
            chain(
                gset("textoEntrada", text("")),
                gset("textoTraducido", text("")),
                setp("TextBox", "txtEntrada", "Text", text("")),
                setp("TextBox", "txtTraduccion", "Text", text("")),
                setp("Button", "btnTraducir", "Enabled", boolean(True)),
                setp("Button", "btnTraducir", "Text", text("Traducir")),
                setp("Button", "btnTraducir", "BackgroundColor", color_teal()),
                call("Notifier", "Notifier1", "DismissProgressDialog"),
                proc_call("ActualizarContador"),
                proc_call("MostrarGuia"),
            ),
            760,
            520,
            note="TRADUCCIÓN — Limpiar",
        )
    )

    # HISTORIAL
    blocks.append(
        proc_def(
            "GuardarHistorial",
            chain(
                insert_item(
                    gget("historial"),
                    num(1),
                    make_list(
                        gget("textoEntrada"),
                        gget("idiomaOrigen"),
                        gget("idiomaDestino"),
                        gget("textoTraducido"),
                    ),
                ),
                iff(
                    gt(list_length(gget("historial")), num(8)),
                    remove_item(gget("historial"), list_length(gget("historial"))),
                ),
                call("TinyDB", "TinyDB1", "StoreValue", text("historial"), gget("historial")),
                proc_call("CargarHistorial"),
            ),
            1160,
            20,
            note="HISTORIAL — Guardar",
        )
    )

    blocks.append(
        proc_def(
            "CargarHistorial",
            chain(
                gset(
                    "historial",
                    call("TinyDB", "TinyDB1", "GetValue", text("historial"), empty_list()),
                ),
                gset("vistaHistorial", empty_list()),
                foreach(
                    "item",
                    gget("historial"),
                    add_item(
                        gget("vistaHistorial"),
                        join(
                            select_item(lget("item"), num(1)),
                            text(" → "),
                            select_item(lget("item"), num(4)),
                            text("  ·  "),
                            lookup_pairs(
                                select_item(lget("item"), num(2)),
                                gget("paresCodigo"),
                                text("?"),
                            ),
                            text("-"),
                            lookup_pairs(
                                select_item(lget("item"), num(3)),
                                gget("paresCodigo"),
                                text("?"),
                            ),
                        ),
                    ),
                ),
                setp("ListView", "lstRecientes", "Elements", gget("vistaHistorial")),
                iff(
                    list_empty(gget("historial")),
                    chain(
                        setp(
                            "Label",
                            "lblSinRecientes",
                            "Text",
                            text("Todavía no hay traducciones.\nCuando traduzcas, aparecerán aquí."),
                        ),
                        setp("Label", "lblSinRecientes", "Visible", boolean(True)),
                        setp("ListView", "lstRecientes", "Visible", boolean(False)),
                        setp("Button", "btnBorrarHistorial", "Visible", boolean(False)),
                        setp("Label", "lblAyudaHistorial", "Visible", boolean(False)),
                    ),
                    chain(
                        setp("Label", "lblSinRecientes", "Text", text("")),
                        setp("Label", "lblSinRecientes", "Visible", boolean(False)),
                        setp("ListView", "lstRecientes", "Visible", boolean(True)),
                        setp("Button", "btnBorrarHistorial", "Visible", boolean(True)),
                        setp("Label", "lblAyudaHistorial", "Visible", boolean(True)),
                    ),
                ),
            ),
            1160,
            420,
            note="HISTORIAL — Cargar",
        )
    )

    # FRASE DEL DÍA
    blocks.append(
        proc_def(
            "MostrarFraseDelDia",
            chain(
                iff(
                    land(
                        land(
                            gt(gget("indiceFrase"), num(0)),
                            lnot(gt(gget("indiceFrase"), list_length(gget("listaFrases")))),
                        ),
                        land(
                            gt(position_in(gget("idiomaOrigen"), gget("listaIdiomas")), num(0)),
                            gt(position_in(gget("idiomaDestino"), gget("listaIdiomas")), num(0)),
                        ),
                    ),
                    chain(
                        gset("fraseActual", select_item(gget("listaFrases"), gget("indiceFrase"))),
                        setp(
                            "Label",
                            "lblFrase",
                            "Text",
                            join(
                                text('"'),
                                select_item(
                                    gget("fraseActual"),
                                    position_in(gget("idiomaDestino"), gget("listaIdiomas")),
                                ),
                                text('"\n\nEn '),
                                gget("idiomaOrigen"),
                                text(':\n"'),
                                select_item(
                                    gget("fraseActual"),
                                    position_in(gget("idiomaOrigen"), gget("listaIdiomas")),
                                ),
                                text('"'),
                            ),
                        ),
                    ),
                )
            ),
            1560,
            20,
            note="FRASE DEL DÍA",
        )
    )

    # ESTADO Y VALIDACIONES
    blocks.append(
        proc_def(
            "ReiniciarReloj",
            chain(
                setp("Clock", "RelojEstado", "TimerEnabled", boolean(False)),
                setp("Clock", "RelojEstado", "TimerEnabled", boolean(True)),
            ),
            1960,
            20,
            note="ESTADO — Reloj",
        )
    )
    blocks.append(
        proc_def(
            "MostrarGuia",
            chain(
                setp("Clock", "RelojEstado", "TimerEnabled", boolean(False)),
                iff(
                    empty_text(trim(getp("TextBox", "txtTraduccion", "Text"))),
                    chain(
                        setp("Label", "lblEstado", "Text", text(HINT_ESTADO)),
                        setp("Label", "lblEstado", "TextColor", color_muted()),
                    ),
                    chain(
                        setp(
                            "Label",
                            "lblEstado",
                            "Text",
                            text("Puedes escuchar, compartir o traducir otro texto."),
                        ),
                        setp("Label", "lblEstado", "TextColor", color_muted()),
                    ),
                ),
            ),
            1960,
            180,
            note="ESTADO — Guía",
        )
    )
    blocks.append(
        proc_def(
            "MostrarAviso",
            chain(
                setp("Label", "lblEstado", "Text", lget("mensaje")),
                setp("Label", "lblEstado", "TextColor", color_error()),
                proc_call("ReiniciarReloj"),
            ),
            1960,
            340,
            args=["mensaje"],
            note="ESTADO — Aviso",
        )
    )
    blocks.append(
        proc_def(
            "MostrarError",
            chain(
                setp("Label", "lblEstado", "Text", lget("mensaje")),
                setp("Label", "lblEstado", "TextColor", color_error()),
                proc_call("ReiniciarReloj"),
                call("Notifier", "Notifier1", "ShowAlert", lget("mensaje")),
            ),
            1960,
            520,
            args=["mensaje"],
            note="ESTADO — Error",
        )
    )
    blocks.append(
        proc_def(
            "MostrarInfo",
            chain(
                setp("Label", "lblEstado", "Text", lget("mensaje")),
                setp("Label", "lblEstado", "TextColor", color_ok()),
                proc_call("ReiniciarReloj"),
            ),
            1960,
            740,
            args=["mensaje"],
            note="ESTADO — Info",
        )
    )
    blocks.append(
        proc_def(
            "ActualizarContador",
            chain(
                setp(
                    "Label",
                    "lblContador",
                    "Text",
                    join(text_length(getp("TextBox", "txtEntrada", "Text")), text("")),
                )
            ),
            1960,
            920,
            note="ENTRADA — Contador",
        )
    )
    blocks.append(
        proc_def(
            "RestaurarBotonTraducir",
            chain(
                setp("Button", "btnTraducir", "Enabled", boolean(True)),
                setp("Button", "btnTraducir", "Text", text("Traducir")),
                setp("Button", "btnTraducir", "BackgroundColor", color_teal()),
                call("Notifier", "Notifier1", "DismissProgressDialog"),
            ),
            1960,
            1080,
            note="TRADUCCIÓN — Botón",
        )
    )
    blocks.append(
        proc_def(
            "RestaurarDesdeHistorial",
            iff(
                gt(getp("ListView", "lstRecientes", "SelectionIndex"), num(0)),
                chain(
                    gset(
                        "itemActual",
                        select_item(
                            gget("historial"),
                            getp("ListView", "lstRecientes", "SelectionIndex"),
                        ),
                    ),
                    setp(
                        "TextBox",
                        "txtEntrada",
                        "Text",
                        select_item(gget("itemActual"), num(1)),
                    ),
                    setp(
                        "Spinner",
                        "spnOrigen",
                        "Selection",
                        select_item(gget("itemActual"), num(2)),
                    ),
                    setp(
                        "Spinner",
                        "spnDestino",
                        "Selection",
                        select_item(gget("itemActual"), num(3)),
                    ),
                    setp(
                        "TextBox",
                        "txtTraduccion",
                        "Text",
                        select_item(gget("itemActual"), num(4)),
                    ),
                    gset("textoEntrada", select_item(gget("itemActual"), num(1))),
                    gset("textoTraducido", select_item(gget("itemActual"), num(4))),
                    proc_call("ActualizarIdiomas"),
                    proc_call("MostrarFraseDelDia"),
                    proc_call("ActualizarContador"),
                    proc_call(
                        "MostrarInfo",
                        [("mensaje", text("Traducción restaurada."))],
                    ),
                ),
            ),
            1960,
            1280,
            note="HISTORIAL — Restaurar",
        )
    )
    blocks.append(
        proc_def(
            "UsarFraseDelDia",
            iff(
                lnot(list_empty(gget("fraseActual"))),
                chain(
                    setp(
                        "TextBox",
                        "txtEntrada",
                        "Text",
                        select_item(
                            gget("fraseActual"),
                            position_in(gget("idiomaOrigen"), gget("listaIdiomas")),
                        ),
                    ),
                    gset("textoEntrada", getp("TextBox", "txtEntrada", "Text")),
                    proc_call("ActualizarContador"),
                    proc_call(
                        "MostrarInfo",
                        [("mensaje", text("Frase lista para traducir."))],
                    ),
                ),
            ),
            1960,
            1680,
            note="FRASE — Usar",
        )
    )
    blocks.append(
        proc_def(
            "OtraFraseDelDia",
            chain(
                gset("indiceFrase", randint(num(1), list_length(gget("listaFrases")))),
                proc_call("MostrarFraseDelDia"),
                proc_call("MostrarInfo", [("mensaje", text("Nueva frase del día."))]),
            ),
            1960,
            1920,
            note="FRASE — Otra",
        )
    )

    # EVENTS
    blocks.append(
        event(
            "Form",
            "Screen1",
            "Initialize",
            chain(
                proc_call("PrepararIdiomas"),
                setp("Spinner", "spnOrigen", "Elements", gget("listaIdiomas")),
                setp("Spinner", "spnDestino", "Elements", gget("listaIdiomas")),
                setp("Spinner", "spnOrigen", "SelectionIndex", num(1)),
                setp("Spinner", "spnDestino", "SelectionIndex", num(2)),
                gset("indiceFrase", randint(num(1), list_length(gget("listaFrases")))),
                proc_call("ActualizarIdiomas"),
                proc_call("CargarHistorial"),
                proc_call("MostrarFraseDelDia"),
                proc_call("LimpiarCampos"),
            ),
            20,
            1120,
            note="INICIO",
        )
    )

    blocks.append(
        event(
            "Spinner",
            "spnOrigen",
            "AfterSelecting",
            chain(proc_call("ActualizarIdiomas"), proc_call("MostrarFraseDelDia")),
            360,
            1280,
            note="IDIOMAS — Origen",
        )
    )
    blocks.append(
        event(
            "Spinner",
            "spnDestino",
            "AfterSelecting",
            chain(proc_call("ActualizarIdiomas"), proc_call("MostrarFraseDelDia")),
            360,
            1460,
            note="IDIOMAS — Destino",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnIntercambiar",
            "Click",
            proc_call("IntercambiarIdiomas"),
            360,
            1640,
            note="IDIOMAS — Intercambio",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnTraducir",
            "Click",
            proc_call("TraducirTexto"),
            760,
            760,
            note="TRADUCCIÓN",
        )
    )
    blocks.append(
        event(
            "Translator",
            "Traductor",
            "GotTranslation",
            chain(
                proc_call("RestaurarBotonTraducir"),
                iff(
                    land(
                        eq(lget("responseCode"), text("200")),
                        lnot(empty_text(trim(lget("translation")))),
                    ),
                    chain(
                        gset("textoTraducido", lget("translation")),
                        setp("TextBox", "txtTraduccion", "Text", gget("textoTraducido")),
                        proc_call("GuardarHistorial"),
                        proc_call("MostrarInfo", [("mensaje", text("Traducción lista."))]),
                    ),
                    chain(
                        gset("textoTraducido", text("")),
                        setp("TextBox", "txtTraduccion", "Text", text("")),
                        proc_call(
                            "MostrarError",
                            [
                                (
                                    "mensaje",
                                    text("No se pudo traducir.\nRevisa internet e inténtalo de nuevo."),
                                )
                            ],
                        ),
                    ),
                ),
            ),
            760,
            940,
            note="TRADUCCIÓN — Resultado",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnHablar",
            "Click",
            chain(
                proc_call("ActualizarIdiomas"),
                proc_call("MostrarInfo", [("mensaje", text("Habla ahora..."))]),
                call("SpeechRecognizer", "ReconocimientoDeVoz", "GetText"),
            ),
            2360,
            20,
            note="VOZ — Reconocimiento",
        )
    )
    blocks.append(
        event(
            "SpeechRecognizer",
            "ReconocimientoDeVoz",
            "AfterGettingText",
            iff(
                lnot(lget("partial")),
                iff(
                    empty_text(trim(lget("result"))),
                    proc_call(
                        "MostrarError",
                        [
                            (
                                "mensaje",
                                text("No se reconoció la voz.\nInténtalo de nuevo."),
                            )
                        ],
                    ),
                    chain(
                        setp("TextBox", "txtEntrada", "Text", lget("result")),
                        gset("textoEntrada", lget("result")),
                        proc_call("ActualizarContador"),
                        proc_call("TraducirTexto"),
                    ),
                ),
            ),
            2360,
            220,
            note="VOZ — Resultado",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnEscuchar",
            "Click",
            iff(
                empty_text(trim(getp("TextBox", "txtTraduccion", "Text"))),
                proc_call(
                    "MostrarAviso",
                    [("mensaje", text("Primero traduce un texto."))],
                ),
                chain(
                    proc_call("ActualizarIdiomas"),
                    call("TextToSpeech", "TextoAVoz", "Speak", getp("TextBox", "txtTraduccion", "Text")),
                    proc_call("MostrarInfo", [("mensaje", text("Reproduciendo traducción..."))]),
                ),
            ),
            2360,
            620,
            note="VOZ — Texto a voz",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnCopiar",
            "Click",
            iff(
                empty_text(trim(getp("TextBox", "txtTraduccion", "Text"))),
                proc_call(
                    "MostrarAviso",
                    [("mensaje", text("Primero traduce un texto."))],
                ),
                chain(
                    call("Sharing", "Compartir", "ShareMessage", getp("TextBox", "txtTraduccion", "Text")),
                    proc_call(
                        "MostrarInfo",
                        [("mensaje", text("Elige cómo compartir o copiar."))],
                    ),
                ),
            ),
            2360,
            960,
            note="TRADUCCIÓN — Compartir",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnLimpiar",
            "Click",
            proc_call("LimpiarCampos"),
            760,
            1480,
        )
    )
    blocks.append(
        event(
            "TextBox",
            "txtEntrada",
            "GotFocus",
            proc_call("ActualizarContador"),
            760,
            1640,
            note="ENTRADA — Foco",
        )
    )
    blocks.append(
        event(
            "TextBox",
            "txtEntrada",
            "LostFocus",
            proc_call("ActualizarContador"),
            760,
            1780,
            note="ENTRADA — Salida",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnUsarFrase",
            "Click",
            proc_call("UsarFraseDelDia"),
            1560,
            420,
            note="FRASE — Usar",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnOtraFrase",
            "Click",
            proc_call("OtraFraseDelDia"),
            1560,
            560,
            note="FRASE — Otra",
        )
    )
    blocks.append(
        event(
            "Button",
            "btnBorrarHistorial",
            "Click",
            call(
                "Notifier",
                "Notifier1",
                "ShowChooseDialog",
                text("Esto elimina las traducciones recientes guardadas en el teléfono."),
                text("¿Vaciar historial?"),
                text("Vaciar"),
                text("Cancelar"),
                boolean(True),
            ),
            1160,
            980,
            note="HISTORIAL — Eliminar",
        )
    )
    blocks.append(
        event(
            "Notifier",
            "Notifier1",
            "AfterChoosing",
            iff(
                eq(lget("choice"), text("Vaciar")),
                chain(
                    gset("historial", empty_list()),
                    call("TinyDB", "TinyDB1", "StoreValue", text("historial"), gget("historial")),
                    proc_call("CargarHistorial"),
                    proc_call("MostrarInfo", [("mensaje", text("Historial vacío."))]),
                ),
            ),
            1160,
            1220,
        )
    )
    blocks.append(
        event(
            "ListView",
            "lstRecientes",
            "AfterPicking",
            proc_call("RestaurarDesdeHistorial"),
            1160,
            1480,
            note="HISTORIAL — Restaurar",
        )
    )
    blocks.append(
        event(
            "Clock",
            "RelojEstado",
            "Timer",
            chain(
                setp("Clock", "RelojEstado", "TimerEnabled", boolean(False)),
                proc_call("MostrarGuia"),
            ),
            2360,
            1320,
            note="ESTADO — Limpiar",
        )
    )
    blocks.append(
        event(
            "Form",
            "Screen1",
            "ErrorOccurred",
            chain(
                proc_call("RestaurarBotonTraducir"),
                iff(
                    eq(lget("functionName"), text("GetText")),
                    proc_call(
                        "MostrarError",
                        [
                            (
                                "mensaje",
                                text("No se reconoció la voz.\nInténtalo de nuevo."),
                            )
                        ],
                    ),
                    iff(
                        eq(lget("functionName"), text("RequestTranslation")),
                        proc_call(
                            "MostrarError",
                            [
                                (
                                    "mensaje",
                                    text("No se pudo traducir.\nRevisa internet e inténtalo de nuevo."),
                                )
                            ],
                        ),
                    ),
                ),
            ),
            20,
            1750,
            note="VALIDACIONES — Errores",
        )
    )

    return '<xml xmlns="http://www.w3.org/1999/xhtml">\n' + "\n".join(blocks) + "\n</xml>"


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def make_icon() -> bytes:
    w = h = 128
    rows = []
    for y in range(h):
        row = [0]
        for x in range(w):
            cx, cy = 63.5, 60.0
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5
            sdx, sdy = x - 67.0, y - 71.0
            sdist = (sdx * sdx + sdy * sdy) ** 0.5
            r, g, b, a = 230, 238, 243, 0
            if sdist <= 64:
                fade = max(0.0, 1.0 - sdist / 64.0)
                a = int(80 * fade * fade)
                r, g, b = 8, 18, 30
            if dist <= 62:
                nx, ny = dx / 62.0, dy / 62.0
                light = max(0.0, min(1.0, 0.52 + (-nx * 0.38 - ny * 0.48)))
                if dist <= 50:
                    base = (14, 186, 168)
                    deep = (8, 78, 74)
                else:
                    base = (16, 42, 66)
                    deep = (6, 16, 28)
                r = int(deep[0] + (base[0] - deep[0]) * light)
                g = int(deep[1] + (base[1] - deep[1]) * light)
                b = int(deep[2] + (base[2] - deep[2]) * light)
                a = 255
                hx, hy = x - 46, y - 42
                if (hx * hx + hy * hy) ** 0.5 < 15 and dist <= 50:
                    r = min(255, r + 58)
                    g = min(255, g + 46)
                    b = min(255, b + 34)
                if 30 <= x <= 76 and 36 <= y <= 72:
                    r, g, b = 255, 255, 255
                if 36 <= x <= 70 and 42 <= y <= 66:
                    r, g, b = 18, 168, 154
                if 56 <= x <= 102 and 58 <= y <= 96:
                    r, g, b = 255, 247, 237
                if 62 <= x <= 96 and 64 <= y <= 90:
                    r, g, b = 16, 42, 66
            row.extend((r, g, b, a))
        rows.append(bytes(row))
    raw = b"".join(rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )


LEEME = """Traductor global
================

Proyecto MIT App Inventor listo para importar.

Cómo importarlo
---------------
1. Entra a https://ai2.appinventor.mit.edu
2. Projects > Import project (.aia) from my computer
3. Elige TraductorGlobal.aia
4. Conecta el Companion o empaqueta la app (Build)

Qué hay de nuevo en la interfaz
-------------------------------
- Encabezado en capas, logo en marco y tarjeta de idiomas flotando sobre el hero.
- Tarjetas con acento lateral y sombra inferior para dar relieve.
- Campos hundidos (pozo) y botones con “labio” inferior.
- Estados en pantalla: guía, aviso, éxito o error. Menos ventanas emergentes.
- Al dictar, traduce automáticamente.
- Toca un ítem reciente para restaurar texto e idiomas.
- Frase del día: “Otra” y “Usar esta frase”.
- Compartir abre la hoja del sistema; mantén pulsado el resultado para copiar.

Qué hace
--------
- Traduce entre 8 idiomas: Español, English, Français, Português,
  Deutsch, 中文, हिन्दी y العربية.
- Escribe texto o dicta con 🎤 Dictar.
- Intercambia idiomas con ⇄ (también intercambia los textos).
- Escucha la traducción con 🔊.
- Comparte el resultado o cópialo con pulsación larga.
- Guarda recientes en TinyDB (siguen ahí al cerrar la app).
- Muestra una frase del día interna, sin APIs extra.

Componentes reales usados
-------------------------
- Translator (MIT, sucesor de YandexTranslate)
- SpeechRecognizer
- TextToSpeech
- TinyDB
- Notifier (alertas, confirmación y progreso)
- Clock (limpia el mensaje de estado)
- Sharing
- Spinner, TextBox, Button, Label, ListView, Image

Traducción
----------
Usa el componente Translator de MIT App Inventor.
El idioma se envía como origen-destino, por ejemplo es-en.
MIT rellena la ApiKey al usar su servidor. No hace falta
una clave externa. La app necesita Internet.

Si al probar Companion la traducción falla:
1. En el diseñador selecciona Traductor.
2. Comprueba que MIT haya rellenado ApiKey.
3. Si está vacía, elimina Traductor, vuelve a añadir
   Translator desde Media y renómbralo a Traductor.

Copiar resultado
----------------
MIT App Inventor no incluye un bloque universal de portapapeles
en todas las versiones. Esta app usa dos alternativas compatibles:

1. El resultado está en un TextBox de solo lectura: mantén pulsado
   el texto traducido y elige Copiar.
2. El botón Compartir abre Sharing.ShareMessage (hoja de compartir
   del sistema, donde también puedes copiar).

Voz
---
El reconocimiento usa SpeechRecognizer.Language según el idioma
de origen (es-ES, en-US, fr-FR, pt-BR, de-DE, zh-CN, hi-IN, ar-SA).
TextoAVoz usa Language/Country del idioma de destino.
El dispositivo debe tener esas voces e idiomas instalados.
Tras dictar, la app traduce sola.

Historial
---------
TinyDB etiqueta: historial
Cada ítem: texto original, idioma origen, idioma destino, traducción.
Se muestran las últimas 8. Vaciar pide confirmación.
Tocar un ítem restaura la traducción en pantalla.

Pruebas sugeridas
-----------------
Español → English : Hola → Hello
English → Español : Hello → Hola
Español → Français : Hola → Bonjour
Español → Português : Hola → Olá
Español → Deutsch : Hola → Hallo
También 中文, हिन्दी y العربية como origen o destino.
Toca un recorte reciente y comprueba que se restaura.
"""


PROPERTIES = """#
#Fri Sep 18 12:00:00 UTC 2026
sizing=Responsive
color.primary.dark=&HFF081526
color.primary=&HFF102A44
color.accent=&HFF12B39A
aname=Traductor global
defaultfilescope=App
main=appinventor.ai_user.TraductorGlobal.Screen1
source=../src
actionbar=False
useslocation=False
assets=../assets
build=../build
icon=icon.png
name=TraductorGlobal
showlistsasjson=True
theme=AppTheme.Light
versioncode=3
versionname=1.2
"""


def main() -> None:
    scm = build_scm()
    bky = build_bky()
    icon = make_icon()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("youngandroidproject/project.properties", PROPERTIES)
        zf.writestr(f"{SRC_DIR}/Screen1.scm", scm)
        zf.writestr(f"{SRC_DIR}/Screen1.bky", bky)
        zf.writestr("assets/icon.png", icon)
        zf.writestr("assets/LEEME.txt", LEEME)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
