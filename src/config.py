
from dataclasses import dataclass
import yaml
#this came to me due to our lord and saviour chatgpt. i will think about if this is bullshit later on and hate myself for it.

@dataclass(frozen=True)
class General:
    max_attempts: int


@dataclass(frozen=True)
class OfflineMode:
    offline_mode_enabled: bool
    card_json: dict

@dataclass(frozen=True)
class ApiOptions:
    request_timeout_in_s: int
    random_card_uri: str
    max_number_faces: int
    creature_filter: str
    manavalue_filter: str
    set_exclusion: str
    sets_to_exclude: list[str]
    splitcard_layouts: list[str]
    layout_edgecases: list[str]

@dataclass(frozen=True)
class Printer:
    backend: str
    win_printer_name: str
    VID: int
    PID: int
    print_image: bool
    print_text: bool
    print_oracle_qr: bool
    max_img_width_in_px: int
    img_print_implementation: str

@dataclass(frozen=True)
class Debug:
    debug_mode_enabled: bool
    test_query_options: str


@dataclass(frozen=True)
class ImageOptions:
    default_img_mode: bool
    img_default_fetch_type: str
    img_draw_type: str
    img_width: int
    img_height: int


@dataclass(frozen=True)
class Config:
    general: General
    offline: OfflineMode
    api: ApiOptions
    debug: Debug
    image: ImageOptions
    printer: Printer

def load_config(path: str = "config.yaml") -> Config:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    return Config(
        general=General(**raw["general"]),
        offline=OfflineMode(**raw["offline"]),
        api=ApiOptions(**raw["api_options"]),
        debug=Debug(**raw["debug"]),
        image=ImageOptions(**raw["image_options"]),
        printer=Printer(**raw["printer"])
    )
