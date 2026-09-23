# Se ejecuta luego de las migraciones y antes de abrir el puerto HTTP.
marker = Rails.root.join('files', '.admin-bootstrap-v1')

unless File.exist?(marker)
  User.transaction do
    begin
      Redmine::DefaultData::Loader.load('es')
    rescue Redmine::DefaultData::DataAlreadyLoaded
      # Conservar tipos de tickets, estados y roles existentes.
    end

    admin = User.find_or_initialize_by(login: 'admin')
    admin.firstname = 'Administrador'
    admin.lastname = 'Redmine'
    admin.mail = ENV.fetch('REDMINE_ADMIN_EMAIL')
    admin.admin = true
    admin.status = User::STATUS_ACTIVE
    admin.language = 'es'
    admin.password = ENV.fetch('REDMINE_ADMIN_PASSWORD')
    admin.password_confirmation = ENV.fetch('REDMINE_ADMIN_PASSWORD')
    admin.must_change_passwd = false
    admin.save!

    Setting.rest_api_enabled = '1'
    Setting.default_language = 'es'
  end

  File.write(marker, "initialized\n")
  puts 'Administrador de Redmine y API REST inicializados.'
end
