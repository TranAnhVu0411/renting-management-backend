document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input[data-thousands]").forEach((input) => {
    const ts = input.dataset.thousandSep || ",";
    const ds = input.dataset.decimalSep || ".";

    const isKept = (ch) => /\d/.test(ch) || ch === ds;
    const clean = (s) => [...s].filter(isKept).join("");

    const format = (raw) => {
      const [int, ...rest] = clean(raw).split(ds); // keep only first decimal dot
      const dec = rest.length ? ds + rest.join("") : "";
      return int.replace(/\B(?=(\d{3})+(?!\d))/g, ts) + dec;
    };

    input.addEventListener("input", () => {
      const pos = input.selectionStart;
      const before = clean(input.value.slice(0, pos)).length;
      input.value = format(input.value);

      let count = 0, newPos = 0;
      while (newPos < input.value.length && count < before) {
        if (isKept(input.value[newPos])) count++;
        newPos++;
      }
      input.setSelectionRange(newPos, newPos);
    });
  });
});