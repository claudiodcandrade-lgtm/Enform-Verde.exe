"""Synthetic IFN-like fixtures only; NEVER use as field observations."""
import csv
import hashlib
import io
import math
import unittest

from tools.ifn_agb_cross_state_diagnostics import evaluate

COLUMNS = [
    "bioma", "uf", "ua", "tipologia_da_vegetacao", "classe_uso_da_terra",
    "agb_mg_ha", "source_equation", "equation_choice_audited",
    "ibge_fitophysiognomy_verified", "sar_pair_eligible",
    "scientifically_validated",
]
RAW_SHA = "a" * 64


def rows():
    return [
        {
            "bioma":"Amazônia", "uf":uf, "ua":f"UA{j}",
            "tipologia_da_vegetacao":"Floresta Natural",
            "classe_uso_da_terra":"Floresta Natural",
            "agb_mg_ha":str(base + j * 10),
            "source_equation":"AGB_Chave",
            "equation_choice_audited":"false",
            "ibge_fitophysiognomy_verified":"false",
            "sar_pair_eligible":"false",
            "scientifically_validated":"false",
        }
        for uf, base in (("PA",0),("AM",20),("AC",40))
        for j in (1,2)
    ]


def encode(data):
    output=io.StringIO(newline="")
    writer=csv.DictWriter(output,fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(data)
    raw=output.getvalue().encode("utf-8")
    return raw,hashlib.sha256(raw).hexdigest()


def report(data):
    raw,digest=encode(data)
    return evaluate(raw,digest,raw_ifn_sha256=RAW_SHA)


class IFNAGBCrossStateTests(unittest.TestCase):
    def test_leave_state_out_metrics_are_computed_from_distinct_ua(self):
        r=report(rows())
        self.assertEqual(r["candidate_ua_count"],6)
        self.assertEqual(r["strata_count"],1)
        self.assertEqual(r["strata_with_transfer_diagnostic"],1)
        self.assertEqual(r["heldout_state_folds"],3)
        st=r["strata"][0]
        self.assertEqual(st["source_state_count"],3)
        self.assertEqual(st["heldout_ua_count"],6)
        self.assertAlmostEqual(st["transfer_rmse_mg_ha"],25)
        self.assertAlmostEqual(st["transfer_mae_mg_ha"],65/3)
        self.assertAlmostEqual(st["transfer_bias_mg_ha"],0)
        self.assertEqual({f["held_out_uf"] for f in st["folds"]},{"PA","AM","AC"})
        for f in st["folds"]:
            self.assertTrue(set(f["test_ua_ids"]).isdisjoint(f["train_ua_ids"]))
            self.assertNotIn(f["held_out_uf"],f["train_ufs"])
        self.assertFalse(r["scientifically_homologated"])
        self.assertFalse(r["is_sar_validation"])
        self.assertFalse(r["is_aoi_ci95"])
        self.assertIsNone(r["independent_prediction_interval_coverage"])
        self.assertFalse(st["can_use_for_aoi_carbon"])
        self.assertFalse(st["ibge_fitophysiognomy_verified"])

    def test_two_states_have_no_transfer_metric(self):
        data=[r for r in rows() if r["uf"]!="AC"]
        r=report(data)
        st=r["strata"][0]
        self.assertEqual(st["transfer_error_status"],"not_available")
        self.assertIsNone(st["transfer_rmse_mg_ha"])
        self.assertEqual(st["folds"],[])

    def test_sparse_test_state_is_not_fabricated(self):
        data=[r for r in rows() if not (r["uf"]=="AC" and r["ua"]=="UA2")]
        st=report(data)["strata"][0]
        self.assertEqual(st["heldout_state_count"],2)
        self.assertEqual(st["heldout_ua_count"],4)
        self.assertNotIn("AC",{f["held_out_uf"] for f in st["folds"]})

    def test_duplicate_ua_across_typologies_fails_closed(self):
        data=rows()
        duplicate=dict(data[0],tipologia_da_vegetacao="Savana")
        with self.assertRaisesRegex(ValueError,"duplicated physical"):
            report(data+[duplicate])

    def test_unicode_alias_ua_fails_closed(self):
        data=rows()
        data[1]["ua"]="ｕａ１"
        with self.assertRaisesRegex(ValueError,"duplicated physical"):
            report(data)

    def test_non_audited_flags_must_remain_false(self):
        for key in ("equation_choice_audited","ibge_fitophysiognomy_verified",
                    "sar_pair_eligible","scientifically_validated"):
            data=rows()
            data[0][key]="true"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,"cannot claim"):
                report(data)

    def test_wrong_equation_rejected(self):
        data=rows()
        data[0]["source_equation"]="AGB_Other"
        with self.assertRaisesRegex(ValueError,"cannot claim"):
            report(data)

    def test_negative_nan_infinite_agb_rejected(self):
        for value in ("-1","nan","inf",""):
            data=rows()
            data[0]["agb_mg_ha"]=value
            with self.subTest(value=value), self.assertRaises(ValueError):
                report(data)

    def test_sha_mismatch_and_invalid_source_hash_rejected(self):
        raw,digest=encode(rows())
        with self.assertRaisesRegex(ValueError,"candidate CSV SHA256"):
            evaluate(raw,"f"*64,raw_ifn_sha256=RAW_SHA)
        with self.assertRaisesRegex(ValueError,"official IFN"):
            evaluate(raw,digest,raw_ifn_sha256="fake")

    def test_repeated_ua_with_conflicting_biome_is_not_independent(self):
        data=rows()
        data[1]["bioma"]="Cerrado"
        data[1]["ua"]=data[0]["ua"]
        with self.assertRaisesRegex(ValueError,"duplicated physical"):
            report(data)

    def test_source_typology_never_auto_crosswalks_ibge(self):
        data=rows()
        for r in data:
            r["tipologia_da_vegetacao"]="Floresta Ombrófila Densa"
        st=report(data)["strata"][0]
        self.assertFalse(st["ibge_fitophysiognomy_verified"])
        self.assertFalse(st["can_use_for_aoi_carbon"])

    def test_equal_state_training_weights_not_large_state_sample(self):
        data=rows()
        # Add many more high-AGB observations to one training state.
        for j in range(3,13):
            item=dict(data[0],uf="PA",ua=f"EXTRA{j}",agb_mg_ha="1000")
            data.append(item)
        st=report(data)["strata"][0]
        fold=next(f for f in st["folds"] if f["held_out_uf"]=="AM")
        pa_mean=(10+20+10*1000)/12
        ac_mean=(50+60)/2
        self.assertAlmostEqual(fold["mean_predicted_agb_mg_ha"],(pa_mean+ac_mean)/2)

    def test_empty_state_cannot_be_a_third_holdout_state(self):
        data=rows()
        data[0]["uf"]=""
        with self.assertRaisesRegex(ValueError,"blank physical UF/UA"):
            report(data)

    def test_non_native_land_cover_cannot_enter_ifn_transfer(self):
        data=rows()
        data[0]["classe_uso_da_terra"]="Lavoura"
        with self.assertRaisesRegex(ValueError,"non-native"):
            report(data)

    def test_rehash_of_original_ifn_bytes_is_independent_and_fail_closed(self):
        candidate_raw,candidate_sha=encode(rows())
        original=b"synthetic-only IFN-like source fixture, not observed data"
        official_sha=hashlib.sha256(original).hexdigest()
        verified=evaluate(candidate_raw,candidate_sha,
                          raw_ifn_sha256=official_sha,raw_ifn_bytes=original)
        self.assertTrue(verified["raw_official_ifn_bytes_verified_by_this_tool"])
        with self.assertRaisesRegex(ValueError,"source bytes do not match"):
            evaluate(candidate_raw,candidate_sha,raw_ifn_sha256=official_sha,
                     raw_ifn_bytes=original+b" tampered")
        with self.assertRaisesRegex(ValueError,"source bytes do not match"):
            evaluate(candidate_raw,candidate_sha,raw_ifn_sha256=official_sha,
                     raw_ifn_bytes="not bytes")

    def test_official_source_lineage_recomputed_from_synthetic_panel(self):
        # Synthetic official-format rows, NEVER genuine SFB observations.
        from tools.prepare_ifn_agb_candidates import prepare, COLUMNS as FULL_COLUMNS
        header=("bioma;uf;ua;lon_pc;lat_pc;sanidade;classe_uso_da_terra;"
                "tipologia_da_vegetacao;equacoes;area_ha;agb_media_kg_por_ha;"
                "agb_variancia_por_ua\n")
        lines=[]
        for uf,base in (("PA",0),("AM",20),("AC",40)):
            for j in (1,2):
                lines.append(";".join((
                    "Amazônia",uf,f"UA{j}","-50","-3","Vivas",
                    "Floresta Natural","Floresta Natural","AGB_Chave",
                    "0.1",str((base+j*10)*1000),"0"))+"\n")
        original=(header+"".join(lines)).encode("utf-8")
        original_sha=hashlib.sha256(original).hexdigest()
        candidates,_=prepare(original,original_sha)
        self.assertEqual(len(candidates),6)
        out=io.StringIO(newline="")
        writer=csv.DictWriter(out,fieldnames=FULL_COLUMNS)
        writer.writeheader()
        writer.writerows(candidates)
        canonical=out.getvalue().encode("utf-8")
        result=evaluate(canonical,hashlib.sha256(canonical).hexdigest(),
                        raw_ifn_sha256=original_sha,raw_ifn_bytes=original,
                        verify_source_lineage=True)
        self.assertTrue(result["candidate_lineage_verified_by_recomputation"])
        self.assertFalse(result["scientifically_homologated"])
        self.assertEqual(result["candidate_ua_count"],6)
        self.assertEqual(result["heldout_state_folds"],3)
        # A forged candidate with a freshly recalculated SHA is still rejected.
        altered=canonical.replace(b"10.0",b"11.0",1)
        self.assertNotEqual(altered,canonical)
        with self.assertRaisesRegex(ValueError,"does not match deterministic extraction"):
            evaluate(altered,hashlib.sha256(altered).hexdigest(),
                     raw_ifn_sha256=original_sha,raw_ifn_bytes=original,
                     verify_source_lineage=True)
        # Rehashing a completely unrelated candidate CSV also fails.
        foreign,foreign_sha=encode(rows())
        with self.assertRaisesRegex(ValueError,"does not match deterministic extraction"):
            evaluate(foreign,foreign_sha,raw_ifn_sha256=original_sha,
                     raw_ifn_bytes=original,verify_source_lineage=True)
        with self.assertRaisesRegex(ValueError,"raw IFN bytes required"):
            evaluate(canonical,hashlib.sha256(canonical).hexdigest(),
                     raw_ifn_sha256=original_sha,verify_source_lineage=True)

    def test_blank_or_duplicate_headers_fail(self):
        raw,digest=encode(rows())
        corrupted=raw.replace(b"agb_mg_ha",b"wrong_col")
        with self.assertRaisesRegex(ValueError,"headers"):
            evaluate(corrupted,hashlib.sha256(corrupted).hexdigest(),raw_ifn_sha256=RAW_SHA)
        duplicated=raw.replace(b"bioma,uf,ua",b"bioma,bioma,ua")
        with self.assertRaisesRegex(ValueError,"headers"):
            evaluate(duplicated,hashlib.sha256(duplicated).hexdigest(),raw_ifn_sha256=RAW_SHA)


if __name__=="__main__":
    unittest.main()
