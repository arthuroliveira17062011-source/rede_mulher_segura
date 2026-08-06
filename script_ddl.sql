CREATE DATABASE rede_mulher_segura;

CREATE TABLE LocalOcorrencia(
    id_local SERIAL PRIMARY KEY,
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(50) NOT NULL,
    bairro VARCHAR(100),
    endereco VARCHAR(150)
);

CREATE TABLE InstituicaoApoio(
    id_instituicao SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(100),
    endereco VARCHAR(150),
    cidade VARCHAR(100),
    estado VARCHAR(50)
);

CREATE TABLE Denuncia(
    id_denuncia SERIAL PRIMARY KEY,
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT NOT NULL,
    tipo_violencia VARCHAR(50) NOT NULL,
    data_denuncia DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'Em análise',
    id_local INT,
    FOREIGN KEY(id_local)
        REFERENCES LocalOcorrencia(id_local)
);

 CREATE TABLE Relatorio(
    id_relatorio SERIAL PRIMARY KEY,
    data_emissaao DATE NOT NULL,
    quantidade_denuncias INT NOT NULL,
    observacoes TEXT,
    id_instituicao INT,
    FOREIGN KEY(id_instituicao)
    REFERENCES InstituicaoApoio(id_instituicao)
 );
 