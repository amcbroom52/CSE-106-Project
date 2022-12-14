function lookup(){
    input = $('#input')

    const package = {
        input: input.val()
    }

    fetch(window.location.origin + '/lookup_users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(package)
    })
    .then(response => response.json())
    .then((body) => {
        users = body['users']

        parentDiv = $('#user-results')

        parentDiv.empty()

        users.forEach((item) => {
            userid = item[0]
            username = item[1]
            pfp_filename = item[2]

            if (pfp_filename == null) {
                pfp_filename = 'empty_user.png'
            }

            markup = `
                        <div class="card m-4">
                            <div class="container" href>
                                <div class="row">
                                    <div class="col-5">
                                        <img src="/static/images/${pfp_filename}" class="w-50 rounded-circle p-2">
                                    </div>
                                    <div class="col d-flex align-items-center">
                                        <a href="${window.location.origin + '/profile/' + userid}">${username}</a>
                                    </div>
                                </div>
                            </div>
                        </div>`
            
            parentDiv.append(markup)

        })
    })
}