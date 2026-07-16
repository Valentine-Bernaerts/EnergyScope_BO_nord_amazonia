from esmc.postprocessing.draw_sankey.output_to_sankey_csv import write_sankey_file
from esmc.postprocessing.draw_sankey.print_sankey_values import read_and_process_data
from esmc.postprocessing.draw_sankey.print_sankey_values import generate_sankey

#write_sankey_file(space_id="HL_LL_SA-BN_SA-PA_SA-SC_SA-TJ_SIN_VL", case_study="03_06_real_demands_real_timeseries")
#NOU ABAIX
write_sankey_file(
    space_id = "HL_LL_SA-BN_SA-PA_SA-SC_SA-TJ_SIN_VL",
    case_study = "24_07_2050",

)
#NOU ADALT
filepath = '/Users/roger/PycharmProjects/EnergyScope_Multicell_BO_Roger-main/case_studies/HL_LL_SA-BN_SA-PA_SA-SC_SA-TJ_SIN_VL/24_07_2024_HL_limited_batt/outputs/regional_results/'
num_decimals = 1
link_transparency = 0.5
node_color = '#3F7CAB'

df, labels = read_and_process_data(filepath, num_decimals)
generate_sankey(df, labels, link_transparency, node_color, filepath)


