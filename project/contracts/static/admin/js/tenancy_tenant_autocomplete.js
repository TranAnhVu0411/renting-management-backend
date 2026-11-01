(function () {
  "use strict";

  function init($) {
    function selectedTenantIds(currentSelect) {
      const ids = [];
      $("select[name$='-tenant']").each(function () {
        if (this.name.includes("__prefix__") || this === currentSelect) return;
        if (this.value) ids.push(this.value);
      });
      return ids;
    }

    function patchSelect2(select) {
      const $select = $(select);
      const instance = $select.data("select2");
      if (!instance || !instance.dataAdapter || $select.data("exclude-patched")) return;

      const ajaxOptions = instance.dataAdapter.ajaxOptions;
      if (!ajaxOptions || typeof ajaxOptions.data !== "function") return;

      const originalData = ajaxOptions.data;
      ajaxOptions.data = function (params) {
        const data = originalData.call(this, params);
        data.exclude_tenant_ids = selectedTenantIds(select).join(",");
        return data;
      };
      $select.data("exclude-patched", true);
    }

    $(document).on("select2:opening", "select[name$='-tenant']", function () {
      patchSelect2(this);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const $ = (window.django && window.django.jQuery) || window.jQuery;
    if (!$) {
      console.error("exclude_selected_tenants.js: jQuery not found");
      return;
    }
    init($);
  });
})();