document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll("input[data-thousands]");

  const format = (raw) => {
    let clean = raw.replace(/[^\d.]/g, "");           // drop letters/symbols
    const [int, ...rest] = clean.split(".");           // keep only first dot
    const dec = rest.length ? "." + rest.join("") : "";
    return int.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + dec;
  };

  inputs.forEach((input) => {
    input.addEventListener("input", () => {
      const pos = input.selectionStart;
      // count meaningful chars before the caret
      const before = input.value.slice(0, pos).replace(/[^\d.]/g, "").length;
      input.value = format(input.value);

      // restore caret after the same number of meaningful chars
      let count = 0, newPos = 0;
      while (newPos < input.value.length && count < before) {
        if (/[\d.]/.test(input.value[newPos])) count++;
        newPos++;
      }
      input.setSelectionRange(newPos, newPos);
    });

    // send plain numbers to the server
    input.form?.addEventListener("submit", () => {
      inputs.forEach((i) => (i.value = i.value.replace(/,/g, "")));
    });
  });
});