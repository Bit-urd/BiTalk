const sitePreference = document.documentElement.getAttribute("data-default-appearance");
const userPreference = localStorage.getItem("appearance");

if ((sitePreference === "dark" && userPreference === null) || userPreference === "dark") {
  document.documentElement.classList.add("dark");
}

if (document.documentElement.getAttribute("data-auto-appearance") === "true") {
  if (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches &&
    userPreference !== "light"
  ) {
    document.documentElement.classList.add("dark");
  }
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (event) => {
    if (event.matches) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  });
}

window.addEventListener("DOMContentLoaded", (event) => {
  const switcher = document.getElementById("appearance-switcher");
  const switcherMobile = document.getElementById("appearance-switcher-mobile");

  updateMeta();
  this.updateLogo?.(getTargetAppearance());

  if (switcher) {
    switcher.addEventListener("click", () => {
      document.documentElement.classList.toggle("dark");
      var targetAppearance = getTargetAppearance();
      localStorage.setItem(
        "appearance",
        targetAppearance
      );
      updateMeta();
      this.updateLogo?.(targetAppearance);
    });
    switcher.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      localStorage.removeItem("appearance");
    });
  }
  if (switcherMobile) {
    switcherMobile.addEventListener("click", () => {
      document.documentElement.classList.toggle("dark");
      var targetAppearance = getTargetAppearance();
      localStorage.setItem(
        "appearance",
        targetAppearance
      );
      updateMeta();
      this.updateLogo?.(targetAppearance);
    });
    switcherMobile.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      localStorage.removeItem("appearance");
    });
  }
});


var updateMeta = () => {
  var elem, style;
  elem = document.querySelector('body');
  style = getComputedStyle(elem);
  document.querySelector('meta[name="theme-color"]').setAttribute('content', style.backgroundColor);
}

var updateLogo = (targetAppearance) => {
  var imgElems = document.querySelectorAll("img.logo");
  var logoContainers = document.querySelectorAll("span.logo");
  
  // Get logo paths from data attributes
  const defaultLogo = document.documentElement.dataset.defaultLogo;
  const secondaryLogo = document.documentElement.dataset.secondaryLogo;
  const defaultAppearance = document.documentElement.dataset.defaultAppearance;
  
  if (defaultLogo && secondaryLogo) {
    const targetLogoPath = targetAppearance == defaultAppearance ? 
      defaultLogo : secondaryLogo;
    
    for (const elem of imgElems) {
      elem.setAttribute("src", targetLogoPath);
    }

    // Handle SVG logos if needed
    if (targetLogoPath.endsWith('.svg')) {
      fetch(targetLogoPath)
        .then(response => response.text())
        .then(svgContent => {
          for (const container of logoContainers) {
            container.innerHTML = svgContent;
          }
        });
    }
  }
  for (const container of logoContainers) {
    container.innerHTML = targetContent;
  }
  {{ end }}
}
{{ end }}
{{- end }}

var getTargetAppearance = () => {
  return document.documentElement.classList.contains("dark") ? "dark" : "light"
}

window.addEventListener("DOMContentLoaded", (event) => {
  const scroller = document.getElementById("top-scroller");
  const footer = document.getElementById("site-footer");
  if(scroller && footer && scroller.getBoundingClientRect().top > footer.getBoundingClientRect().top) {
    scroller.hidden = true;
  }

  // Weekly-specific appearance features
  if (window.location.pathname.includes('/weekly/')) {
    document.documentElement.classList.add('weekly-content');
    // Add weekly-specific theme color
    updateMeta();
  }
});
