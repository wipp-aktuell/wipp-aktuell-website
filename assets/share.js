document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(
    '.article-share [data-share-action="native"]'
  ).forEach(function (button) {
    if (typeof navigator.share === "function") {
      button.hidden = false;
    }
  });
});

document.addEventListener("click", async function (event) {
  const button = event.target.closest(
    ".article-share [data-share-action]"
  );

  if (!button) return;

  const section = button.closest(".article-share");
  const feedback = section.querySelector(".share-feedback");
  const url = button.dataset.shareUrl;
  const action = button.dataset.shareAction;

  if (action === "native") {
    if (typeof navigator.share !== "function") return;

    try {
      await navigator.share({
        title: button.dataset.shareTitle,
        url: url
      });
      feedback.textContent = "";
    } catch (error) {
      if (error.name !== "AbortError") {
        feedback.textContent = "Teilen war nicht möglich.";
      }
    }
    return;
  }

  if (action === "copy") {
    try {
      await navigator.clipboard.writeText(url);
      feedback.textContent = "Link wurde kopiert.";
    } catch (error) {
      feedback.textContent =
        "Link konnte nicht kopiert werden. Bitte die Adresse aus der Browserzeile kopieren.";
    }
  }
});
