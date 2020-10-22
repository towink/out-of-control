import os

testfile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_files")


def _path(file):
    """Internal method for simpler listing of examples."""
    return os.path.join(testfile_dir, file)


bluetooth_prism = _path("bluetooth.prism")
brp_prism = _path("brp.prism")
coin_game_prism = _path("coin_game.prism")
consensus_2_prism = _path("consensus.2.prism")
consensus_4_prism = _path("consensus.4.prism")
consensus_6_prism = _path("consensus.6.prism")
coupon_10_prism = _path("coupon.10-1.prism")
coupon_count_10_prism = _path("coupon_count.10-1.prism")
crowds_prism = _path("crowds.prism")
csma_2_2_prism = _path("csma.2-2.v1.prism")
egl_prism = _path("egl.prism")
fair_exchange_prism = _path("fair_exchange.prism")
firewire_false_prism = _path("firewire.false.prism")
firewire_dl_prism = _path("firewire_dl.prism")
leader_sync_3_2_prism = _path("leader_sync.3-2.prism")
leader_sync_3_8_prism = _path("leader_sync.3-8.prism")
leader_sync_4_8_prism = _path("leader_sync.4-8.prism")
leader_sync_5_3_prism = _path("leader_sync.5-3.prism")
leader_sync_5_4_prism = _path("leader_sync.5-4.prism")
leader_sync_5_8_prism = _path("leader_sync.5-8.prism")
leader_sync_6_8_prism = _path("leader_sync.6-8.prism")
nand_prism = _path("nand.prism")
oscillators_3_6_prism = _path("oscillators.3-6-0.1-1.prism")
oscillators_6_10_prism = _path("oscillators.6-10-0.1-1.prism")
oscillators_6_6_prism = _path("oscillators.6-6-0.1-1.prism")
wlan_0_prism = _path("wlan.0.prism")
zeroconf_prism = _path("zeroconf.prism")
