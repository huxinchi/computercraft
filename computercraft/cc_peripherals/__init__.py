from typing import Callable, Dict, List, Optional


# ============ 用户可扩展的通用存储方块列表 ============
# 完整名称（含命名空间）。用户通过 add_* 函数追加。

INVENTORY_BLOCKS: List[str] = [
    'minecraft:chest',
    'minecraft:furnace',
    'minecraft:barrel',
    'minecraft:hopper',
    'minecraft:dropper',
    'minecraft:dispenser',
    'minecraft:blast_furnace',
    'minecraft:smoker',
    'minecraft:shulker_box',
    'minecraft:brewing_stand',
]

ENERGY_STORAGE_BLOCKS: List[str] = [
    # 默认为空，由用户 add_energy_storage() 添加
]

FLUID_STORAGE_BLOCKS: List[str] = [
    # 默认为空，由用户 add_fluid_storage() 添加
]


# ============ 内部状态：由 register_std_peripherals 填充 ============

_register_fn: Optional[Callable] = None
_factories: Dict[str, Callable] = {}


def _norm(name: str) -> str:
    """补全默认命名空间。'chest' -> 'minecraft:chest'"""
    return name if ':' in name else 'minecraft:' + name


def _make_inv_factory():
    from .inventory import InventoryPeripheral

    def _inv(side, ptype, call):
        p = InventoryPeripheral(side)
        p.TYPE = ptype
        return p
    return _inv


def _make_energy_factory():
    from .energy_storage import EnergyStoragePeripheral

    def _f(side, ptype, call):
        p = EnergyStoragePeripheral(side)
        p.TYPE = ptype
        return p
    return _f


def _make_fluid_factory():
    from .fluid_storage import FluidStoragePeripheral

    def _f(side, ptype, call):
        p = FluidStoragePeripheral(side)
        p.TYPE = ptype
        return p
    return _f


def _try_register(block_type: str, kind: str) -> None:
    """如果 register_std_peripherals 已经跑过，立即把新方块注册到 type_map。"""
    if _register_fn is None:
        return
    factory = _factories.get(kind)
    if factory is None:
        return
    _register_fn(_norm(block_type), factory)


# ============ 用户 API ============

def add_inventory(block_type: str) -> None:
    """注册一个方块类型为 inventory 外设。

    block_type 可带或不带命名空间，例如 'mekanism:personal_chest'
    或 'mekanism_personal_chest'。重复添加同一个名字不会重复注册。
    """
    name = _norm(block_type)
    if name not in INVENTORY_BLOCKS:
        INVENTORY_BLOCKS.append(name)
    _try_register(name, 'inventory')


def add_energy_storage(block_type: str) -> None:
    """注册一个方块类型为 energy_storage 外设。"""
    name = _norm(block_type)
    if name not in ENERGY_STORAGE_BLOCKS:
        ENERGY_STORAGE_BLOCKS.append(name)
    _try_register(name, 'energy_storage')


def add_fluid_storage(block_type: str) -> None:
    """注册一个方块类型为 fluid_storage 外设。"""
    name = _norm(block_type)
    if name not in FLUID_STORAGE_BLOCKS:
        FLUID_STORAGE_BLOCKS.append(name)
    _try_register(name, 'fluid_storage')


# ============ 标准外设注册 ============

def register_std_peripherals(register):
    global _register_fn
    _register_fn = register

    from .command import CommandPeripheral
    from .computer import ComputerPeripheral
    from .drive import DrivePeripheral
    from .modem import WirelessModemPeripheral, WiredModemPeripheral
    from .printer import PrinterPeripheral
    from .speaker import SpeakerPeripheral
    from .term import MonitorPeripheral
    from .workbench import WorkbenchPeripheral
    from .redstone_relay import RedstoneRelayPeripheral

    register('command', CommandPeripheral)
    register('drive', DrivePeripheral)

    def _cmp(side, ptype, call):
        p = ComputerPeripheral(side)
        p.TYPE = ptype
        return p

    for k in ['computer', 'turtle']:
        register(k, _cmp)

    # inventory
    inv_factory = _make_inv_factory()
    _factories['inventory'] = inv_factory
    for k in INVENTORY_BLOCKS:
        register(k, inv_factory)

    # energy_storage
    energy_factory = _make_energy_factory()
    _factories['energy_storage'] = energy_factory
    for k in ENERGY_STORAGE_BLOCKS:
        register(k, energy_factory)

    # fluid_storage
    fluid_factory = _make_fluid_factory()
    _factories['fluid_storage'] = fluid_factory
    for k in FLUID_STORAGE_BLOCKS:
        register(k, fluid_factory)

    def _modem(side, ptype, call):
        if call(b'isWireless').take_bool():
            return WirelessModemPeripheral(side)
        else:
            return WiredModemPeripheral(side)

    register('modem', _modem)
    register('redstone_relay', RedstoneRelayPeripheral)
    register('printer', PrinterPeripheral)
    register('speaker', SpeakerPeripheral)
    register('monitor', MonitorPeripheral)
    register('workbench', WorkbenchPeripheral)