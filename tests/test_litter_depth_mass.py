import unittest

from litter_depth_mass import estimate_litter_carbon_from_depth


def evidence(carbon=True):
    rows=[]
    for unit in range(5):
        for j in range(6):
            row={"record_type":"gravimetric_calibration","biome":"Cerrado",
                 "physiognomy":"Cerrado sensu stricto","region":"MG",
                 "depth_cm":1+j*.2,"dry_mass_g":(10+j*2)*.25,
                 "sample_area_m2":.25,"unit_id":f"CAL-{unit}",
                 "source":"field study","source_url":"https://example.org/study",
                 "institution":"Universidade Federal"}
            if carbon: row["carbon_fraction"]=.43
            rows.append(row)
    for unit in range(5):
        for j in range(5):
            rows.append({"record_type":"ifn_depth","biome":"Cerrado",
                "physiognomy":"Cerrado sensu stricto","region":"MG",
                "depth_cm":1.2+j*.1,"unit_id":f"IFN-{unit}",
                "lon":-45+unit*.1,"lat":-17,"source":"IFN aberto",
                "source_url":"https://dados.florestal.gov.br","institution":"SFB IFN",
                "open_data":True})
    return rows


class LitterDepthMassTests(unittest.TestCase):
    def run_estimate(self, rows):
        return estimate_litter_carbon_from_depth(rows,biome="Cerrado",
            physiognomy="Cerrado sensu stricto",region="MG",
            aoi_lon=-45,aoi_lat=-17,bootstrap_replicates=200)

    def test_matching_calibration_produces_auditable_carbon_estimate(self):
        result=self.run_estimate(evidence())
        self.assertEqual(result["status"],"ESTIMATIVA_EXPERIMENTAL_IFN_GRAVIMETRICA")
        self.assertEqual(result["calibration_point_count"],30)
        self.assertAlmostEqual(result["carbon_fraction"],.43)
        self.assertIsNotNone(result["calculation_trace"]["beta1_g_m2_per_cm"])
        self.assertIn("não é IC95%",result["uncertainty"]["meaning"])

    def test_no_measured_carbon_fraction_returns_mass_but_no_carbon(self):
        result=self.run_estimate(evidence(carbon=False))
        self.assertEqual(result["status"],"MASSA_SECA_ESTIMADA_CARBONO_ND")
        self.assertIsNone(result["mean_tc_ha"])
        self.assertGreater(result["dry_litter_mg_ha"],0)

    def test_mismatched_physiognomy_cannot_calibrate(self):
        rows=evidence()
        for row in rows:
            row["physiognomy"]="Floresta ombrófila densa"
        result=self.run_estimate(rows)
        self.assertEqual(result["status"],"N/D_CONVERSAO_PROFUNDIDADE_SEM_PARES_GRAVIMETRICOS")


if __name__=="__main__": unittest.main()
