document.addEventListener("DOMContentLoaded", function () {
  const inlineSections = document.querySelectorAll(".nested-inline fieldset.module");

  inlineSections.forEach(section => {
    const header = section.querySelector("h2");
    const content = Array.from(section.children).filter(child => !child.matches("h2"));

    if (header && content.length > 0) {
      header.style.cursor = "pointer";
      header.style.userSelect = "none";
      header.style.background = "#f3f3f3";
      header.style.borderBottom = "1px solid #ccc";
      header.style.padding = "4px";

      // Collapse by default
      content.forEach(el => el.style.display = "none");

      header.addEventListener("click", () => {
        const currentlyVisible = content[0].style.display !== "none";
        content.forEach(el => el.style.display = currentlyVisible ? "none" : "block");
      });
    }
  });
});