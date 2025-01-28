document.getElementById("course-form").addEventListener("submit", async (event) => {
    event.preventDefault();
  
    const title = document.getElementById("title").value;
    const duration = document.getElementById("duration").value;
    const audience = document.getElementById("audience").value;
    const numChapters = document.getElementById("numChapters").value;
  
    const planOutput = document.getElementById("course-plan-output");
    const outputSection = document.getElementById("output-section");
  
    planOutput.textContent = "Génération en cours...";
    outputSection.hidden = false;
  
    try {
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer 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`
        },
        body: JSON.stringify({
          model: "gpt-3.5-turbo",
          messages: [
            {
              role: "user",
              content: `
              Crée un plan complet et détaillé pour une formation intitulée "${title}".
              Durée : ${duration}, Public concerné : ${audience}, Nombre de chapitres : ${numChapters}.
              `
            }
          ]
        })
      });
  
      const data = await response.json();
      const plan = data.choices[0].message.content;
  
      planOutput.textContent = plan;
  
      const blob = new Blob([plan], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
  
      const downloadButton = document.getElementById("download-plan");
      downloadButton.href = url;
      downloadButton.download = `${title.replace(/ /g, "_")}_Plan.pdf`;
    } catch (error) {
      planOutput.textContent = "Une erreur est survenue lors de la génération.";
      console.error(error);
    }
  });
  