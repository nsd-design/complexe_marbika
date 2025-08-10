$(document).ready(function () {
	var tabLocation = $("#tableLocation").DataTable({
		ajax: {
			url: '/client/location_reservation/locations/',
			dataSrc: 'data',
		},
		columns: [
			{
				data: null,
				render: function(data, type, row, meta){
					return meta.row + 1;
					}
			},
			{ data: 'locateur' },
			{ data: 'telephone' },
			{ data: 'zone' },
			{ data: 'montant_a_payer' },
			{ data: 'remise' },
			{ data: 'net_paye' },
			{ data: 'date_debut' },
			{ data: 'date_fin' },
			{ data: 'statut' },
			{ data: 'type_location' },
			{ data: 'description' },

		]
	})
	
	function chargerClients($select)
	{
		$.ajax({
			url: '/salon/produits/list_clients/',
			method: 'GET',
			success: function(data){
			$select.empty(); // Vider l'ancien contenu
				$select.append(new Option("-- Selectionner un Client --", "", true, true));
			data.data.forEach(function(client){
				$select.append(new Option(`${client.nom_complet} - ${client.telephone ? client.telephone : ""}`, client.id));
			});
			$select.select2({
				allowClear: true
			});

			$select.trigger('change'); // Mettre à jour le Select2
			},
			error: function(err){
			console.log(err)
			}
		});
	}

	const $selectClientLocation = $("#clients-select")
	const $selectClientReservation = $("#clientsSelectReservation")

	chargerClients($selectClientLocation);
	chargerClients($selectClientReservation);

	function getCSRFToken(){
		const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
		return csrfToken ? csrfToken.value : "";
	}

	// Definir la Date au format annee moise jour
	function normaliserDate(date) {
		if(!(date instanceof Date)){
			date = new Date(date)
		}
		return new Date(date.getFullYear(), date.getMonth(), date.getDate());
	}
  
	$("#zoneForm").on('submit', function(e){
		e.preventDefault();
		let formData = new FormData(this)

		$.ajax({
			url: $("#zoneForm").attr("action"),
			method: "POST",
			data: formData,
			processData: false,
			contentType: false,
			success: function(res){
				if(res.success){
					console.log(res)
					$("#responseMessageZone").text(res.msg)
					$('#responseMessageZone').addClass('bg-success show').fadeIn();
					setTimeout(function(){
						$("#responseMessageZone").removeClass('show bg-success').fadeOut();
					}, 3000)
					$("#zoneForm")[0].reset()
				}
			},
			error: function(err){
				console.log(err)
				$("#responseMessageZone").text(res.msg)
				$('#responseMessageZone').addClass('bg-danger show').fadeIn();
				setTimeout(function(){
					$("#responseMessageZone").removeClass('show bg-danger').fadeOut();
				}, 3000)     
			},
		})
	})
    
	

    $("#submitLocation").on('click', function (e) {
        e.preventDefault();  // Empêche le rechargement de la page

		const id_client = $("#clients-select").val()
		const id_zone = $("#id_zone").val()
		const montant_a_payer = $("#id_montant_a_payer").val()
		const remise = $("#id_montant_reduit").val() || 0
		const date_debut = $("#id_date_debut").val()
		const date_fin = $("#id_date_fin").val()
		const statut = $("#id_statut").val()
		const type_location = $("#id_type_location").val()
		const description = $("#id_description").val()

		// Controler la Date debut de Location par rapport a la date du jour
		const dateDebut = normaliserDate(date_debut);
		const dateFin = normaliserDate(date_fin)
		const today = normaliserDate(new Date());

		if(dateDebut.getTime() < today.getTime()){
			alert("La Date de Début est incorrecte")
			return;
		}

		// Controller la Date de Fin de Location par rapport a la Date de debut
		if(dateFin.getTime() < dateDebut.getTime()){
			alert("La date de fin doit être supérieur ou égale à la date de début");
			return;
		}

		data = {
			id_client,
			id_zone,
			montant_a_payer,
			remise,
			date_debut,
			date_fin,
			statut,
			type_location,
			description,
		}

		if(!data.id_client || !data.id_zone || !data.montant_a_payer || !data.date_debut || !data.date_fin || !data.statut || !data.type_location){
			$("#responseMessageLouer").addClass("show bg-danger").fadeIn().removeClass("bg-success").text("Les champs notés du symbole * sont obligatoires");
			setTimeout(() => $("#responseMessageLouer").removeClass("show").fadeOut(), 3000);
			return;
		}
		

        $.ajax({
            url: $("#locationForm").attr("action"), // Récupère l'URL de l'attribut action
            method: "POST",
			headers: { 'X-CSRFToken': getCSRFToken() },
            data: JSON.stringify(data),
            contentType: "application/json",
            success: function (res) {
				if(res.success){
					
					$("#responseMessageLouer").addClass("show bg-success").fadeIn().removeClass("bg-danger").text(res.msg);
					$("#locationForm")[0].reset(); // Réinitialise le formulaire
				}
            },
            error: function (xhr) {
                let errMsg = xhr.responseJSON?.msg || "Une erreur s'est produite";
                $("#responseMessageLouer").addClass("show bg-danger").fadeIn().removeClass("bg-success").text(errMsg);
            }
        });

        // Cacher le message après 3 secondes
        setTimeout(() => $("#responseMessageLouer").removeClass("show").fadeOut(), 3000);
    });
    
    $("#submitReservation").on('click', function () {
        // e.preventDefault();  // Empêche le rechargement de la page

		const id_client = $("#clientsSelectReservation").val()
		const id_zone = $("#zone_reservation").val()
		const type = $("#id_type").val()
		const statut = $("#id_etat_reservation").val()
		const date_debut = $("#date_debut_reservation").val()
		const date_fin = $("#date_fin_reservation").val()
		const commentaire = $("#id_commentaire").val()

		// Controler la Date debut de Location par rapport a la date du jour
		const dateDebut = normaliserDate(date_debut);
		const dateFin = normaliserDate(date_fin)
		const today = normaliserDate(new Date());

		if(dateDebut.getTime() < today.getTime()){
			alert("La Date de Début est incorrecte")
			return;
		}

		// Controller la Date de Fin de Location par rapport a la Date de debut
		if(dateFin.getTime() < dateDebut.getTime()){
			alert("La date de fin doit être supérieur ou égale à la date de début");
			return;
		}


		data = {
			id_client,
			id_zone,
			type,
			statut,
			date_debut,
			date_fin,
			commentaire,
		}
		
		if(!data.id_client || !data.id_zone || !data.date_debut || !data.date_fin || !data.statut || !data.type){
			$("#responseMessageReservation").addClass("show bg-danger").fadeIn().removeClass("bg-success").text("Les champs notés du symbole * sont obligatoires");
			setTimeout(() => $("#responseMessageReservation").removeClass("show").fadeOut(), 3000);
			return;
		}
		
        $.ajax({
            url: '/client/location_reservation/reserver/',
            method: "POST",
			headers: { 'X-CSRFToken': getCSRFToken() },
            data: JSON.stringify(data),
            contentType: "application/json",
            success: function (res) {
				if(res.success){
					
					$("#responseMessageReservation").addClass("show bg-success").fadeIn().removeClass("bg-danger").text(res.msg);
					$("#clientsSelectReservation").val('')
					$("#zone_reservation").val('')
					$("#id_type").val('')
					$("#id_etat_reservation").val('')
					$("#date_debut_reservation").val('')
					$("#date_fin_reservation").val('')
					$("#id_commentaire").val('')
				}
            },
            error: function (xhr) {
                let errMsg = xhr.responseJSON?.msg || "Une erreur s'est produite";
                $("#responseMessageReservation").addClass("show bg-danger").fadeIn().removeClass("bg-success").text(errMsg);
            }
        });

        // Cacher le message après 3 secondes
        setTimeout(() => $("#responseMessageReservation").removeClass("show").fadeOut(), 3000);
    });
	
});
