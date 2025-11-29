import streamlit as st

# ----------------------------
# Convert input time to microseconds
# ----------------------------
def to_microseconds(value, unit):
    if unit == "ns":
        return value / 1000
    if unit == "us":
        return value
    if unit == "ms":
        return value * 1000
    if unit == "s":
        return value * 1_000_000
    raise ValueError("Unit must be 'ns', 'us', 'ms', 's'")


# ----------------------------
# Convert back from microseconds
# ----------------------------
def from_microseconds(value_us, unit):
    if unit == "ns":
        return value_us * 1000
    if unit == "us":
        return value_us
    if unit == "ms":
        return value_us / 1000
    if unit == "s":
        return value_us / 1_000_000


# ----------------------------
# Compute all WDT intervals (DCO 1-24MHz, DIVM/DIVS 1,2,4,8)
# ----------------------------
def compute_wdt_intervals(desired_us):
    # Simulate DCO frequencies (max 24 MHz)
    dco_freqs = [1_000_000, 2_000_000, 4_000_000, 8_000_000,
                 12_000_000, 16_000_000, 20_000_000, 24_000_000]

    # DIVM/DIVS prescalers
    cs_dividers = {
        "DIV1": 1,
        "DIV2": 2,
        "DIV4": 4,
        "DIV8": 8
    }

    # WDT dividers
    wdt_dividers = {
        "2^6": 2**6,
        "2^9": 2**9,
        "2^13": 2**13,
        "2^15": 2**15,
        "2^19": 2**19,
        "2^23": 2**23,
        "2^27": 2**27,
        "2^31": 2**31
    }

    results = []

    for dco in dco_freqs:
        for divm_name, divm in cs_dividers.items():  # MCLK divider
            mclk = dco / divm
            for divs_name, divs in cs_dividers.items():  # SMCLK divider
                smclk = mclk / divs
                for wdt_name, wdt_div in wdt_dividers.items():
                    t_us = (wdt_div / smclk) * 1_000_000
                    error = abs(t_us - desired_us)
                    results.append({
                        "DCO": dco,
                        "MCLK_DIV": divm_name,
                        "MCLK": mclk,
                        "SMCLK_DIV": divs_name,
                        "SMCLK": smclk,
                        "WDT_DIV": wdt_name,
                        "time_us": t_us,
                        "error_us": error
                    })

    best = min(results, key=lambda x: x["error_us"])
    return results, best


# ----------------------------
# STREAMLIT UI
# ----------------------------
st.title("⏱ MSP430 Watchdog Timer Interval Calculator (DCO 1-24MHz, DIVM/DIVS)")
st.write("Calculează intervalele WDT folosind DCO până la 24 MHz și toate divizările valide.")

# User input
value = st.number_input("Timp dorit:", min_value=0.0, step=0.1)
unit = st.selectbox("Unitate de timp:", ["ns", "us", "ms", "s"])

if st.button("Calculează"):
    desired_us = to_microseconds(value, unit)
    results, best = compute_wdt_intervals(desired_us)

    st.subheader("Rezultate calculate")
    st.dataframe([
        {
            "DCO (Hz)": r["DCO"],
            "MCLK_DIV": r["MCLK_DIV"],
            "MCLK (Hz)": r["MCLK"],
            "SMCLK_DIV": r["SMCLK_DIV"],
            "SMCLK (Hz)": r["SMCLK"],
            "WDT_DIV": r["WDT_DIV"],
            "Time (us)": round(r["time_us"], 3),
            "Error (us)": round(r["error_us"], 3)
        }
        for r in results
    ])

    best_time_converted = from_microseconds(best['time_us'], unit)
    best_error_converted = from_microseconds(best['error_us'], unit)

    st.subheader("Recomandare optimă")
    st.success(
        f"DCO: **{best['DCO']} Hz**\n"
        f"MCLK_DIV: **{best['MCLK_DIV']}** → MCLK = {best['MCLK']} Hz\n"
        f"SMCLK_DIV: **{best['SMCLK_DIV']}** → SMCLK = {best['SMCLK']} Hz\n"
        f"WDT_DIV: **{best['WDT_DIV']}**\n\n"
        f"Timp generat: **{best_time_converted:.6f} {unit}**\n"
        f"Eroare: **{best_error_converted:.6f} {unit}**"
    )

