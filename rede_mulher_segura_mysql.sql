-- ============================================================
-- REDE MULHER SEGURA — Banco de Dados
-- Versão: MySQL
-- Baseado no DER e no Dicionário de Dados do projeto
-- ============================================================

create database if not exists rede_mulher_segura
    character set utf8mb4
    collate utf8mb4_unicode_ci;

use rede_mulher_segura;

-- ------------------------------------------------------------
-- 1. USUARIA
-- ------------------------------------------------------------
create table usuaria (
    id_usuario           int auto_increment primary key,
    nome_completo         varchar(150) not null,
    cpf                   varchar(14) not null unique,
    email                 varchar(150) not null unique,
    telefone_celular      varchar(20) not null unique,
    data_nascimento       date not null,
    endereco_residencia   varchar(255),
    senha_hash            varchar(255) not null,
    frase_chave           varchar(100),
    criado_em             datetime not null default current_timestamp
) engine=InnoDB;

-- senha_hash: senha criptografada para acesso à área segura de provas
-- frase_chave: frase-comando usada para ativar o alerta por voz

-- ------------------------------------------------------------
-- 2. CONTATO_EMERGENCIA
-- ------------------------------------------------------------
create table contato_emergencia (
    id_contato             int auto_increment primary key,
    id_usuario             int not null,
    nome_completo           varchar(150) not null,
    telefone_whatsapp       varchar(20) not null,
    prioridade_notificacao  int not null,
    criado_em               datetime not null default current_timestamp,
    constraint fk_contato_usuario
        foreign key (id_usuario) references usuaria (id_usuario)
        on delete cascade
) engine=InnoDB;

-- prioridade_notificacao: ordem em que o contato é avisado (1 = primeiro)

-- ------------------------------------------------------------
-- 3. OCORRENCIAS_DE_ALERTA
-- ------------------------------------------------------------
create table ocorrencias_de_alerta (
    id_alerta                      int auto_increment primary key,
    id_usuario                     int not null,
    data_hora_ativacao             datetime not null default current_timestamp,
    tipo_ativacao                  enum('botao', 'comando_voz', 'temporizador') not null,
    link_google_maps_localizacao   varchar(500),
    link_compartilhamento          varchar(500),
    constraint fk_alerta_usuario
        foreign key (id_usuario) references usuaria (id_usuario)
        on delete cascade
) engine=InnoDB;

-- tipo_ativacao: como o alerta foi disparado (botão, comando de voz, temporizador sem cancelamento)
-- link_google_maps_localizacao: localização exata registrada no momento do alerta
-- link_compartilhamento: link gerado para compartilhar o alerta (ex: com a polícia)

-- ------------------------------------------------------------
-- 4. MIDIA_PROVAS
-- ------------------------------------------------------------
create table midia_provas (
    id_midia                 int auto_increment primary key,
    id_alerta                int not null,
    id_usuario                int not null,
    tipo_arquivo              enum('audio', 'video', 'imagem') not null,
    caminho_arquivo_nuvem     varchar(500) not null,
    tamanho_arquivo_bytes     bigint not null,
    data_hora_registro        datetime not null default current_timestamp,
    constraint fk_midia_alerta
        foreign key (id_alerta) references ocorrencias_de_alerta (id_alerta)
        on delete cascade,
    constraint fk_midia_usuario
        foreign key (id_usuario) references usuaria (id_usuario)
        on delete cascade
) engine=InnoDB;

-- caminho_arquivo_nuvem: caminho do arquivo no serviço de armazenamento em nuvem escolhido

-- ------------------------------------------------------------
-- 5. CONFIGURACOES_DE_SEGURANCA
-- ------------------------------------------------------------
create table configuracoes_de_seguranca (
    id_configuracao              int auto_increment primary key,
    id_usuario                   int not null unique,
    tempo_temporizador_segundo   int,
    pin_desativado               varchar(20),
    tema_disfarce_padrao         varchar(50) default 'cardapio_restaurante',
    constraint fk_config_usuario
        foreign key (id_usuario) references usuaria (id_usuario)
        on delete cascade
) engine=InnoDB;

-- tempo_temporizador_segundo: tempo (segundos) até o envio automático do alerta se não cancelado
-- pin_desativado: PIN usado para cancelar um alerta disparado por engano
-- tema_disfarce_padrao: tela de disfarce exibida por padrão (ex: cardápio de restaurante)

-- ------------------------------------------------------------
-- ÍNDICES ÚTEIS
-- ------------------------------------------------------------
create index idx_contato_emergencia_usuario on contato_emergencia (id_usuario);
create index idx_ocorrencias_usuario on ocorrencias_de_alerta (id_usuario);
create index idx_midia_alerta on midia_provas (id_alerta);
create index idx_midia_usuario on midia_provas (id_usuario);
