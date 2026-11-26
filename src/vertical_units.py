"""Explicit source vertical unit conversion; not a datum transformation."""
FACTORS={'m':1.0,'us-ft':1200/3937,'ft':.3048}
def factor(unit):
    return FACTORS[unit]
def declared_unit(value):
    s=str(value or '').strip().lower().replace('_',' ')
    if s in ('m','meter','meters','metre','metres'):return 'm'
    if s in ('us survey foot','us survey feet','foot us','feet us','ftus','us-ft','foot us survey','us foot'):return 'us-ft'
    if s in ('international foot','international feet'):return 'ft'
    # 'ft' or 'foot' alone does not distinguish survey and international feet.
    return None
def check_unit(declared,chosen):
    actual=declared_unit(declared)
    if actual and actual!=chosen:raise ValueError(f'Vertical units conflict: source {declared}, selected {chosen}')
