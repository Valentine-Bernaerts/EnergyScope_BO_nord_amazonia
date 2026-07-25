##########################
### OBJECTIVE FUNCTION ###
##########################

# Can choose between TotalGWP and TotalCost
#minimize obj:  sum{c in REGIONS} TotalCost[c] + 260 * (sum{c1 in REGIONS}(Exch_freight[c1]));
#minimize obj:  sum{c in REGIONS} TotalCost[c] + 2000 * (sum{c1 in REGIONS, c2 in REGIONS, i in EXCHANGE_FREIGHT_R, h in HOURS, td in TYPICAL_DAYS}(Exch_extra_freight_imp[c1,c2,i,h,td] + Exch_extra_freight_exp[c1,c2,i,h,td]));
minimize obj:  sum{c in REGIONS} TotalCost[c];

## formula for GWP_op optimization
# sum{c in REGIONS, r in RESOURCES} (GWP_op [c,r]);
# 
